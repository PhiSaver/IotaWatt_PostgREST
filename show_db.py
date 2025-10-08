#!/usr/bin/env python3
"""
Display IoTaWatt data from PostgreSQL database via PostgREST API using JWT authentication.
"""

import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime
from generate_jwt import generate_jwt_token, env_vars

# Load PostgREST configuration from .env file
POSTGREST_PORT = env_vars.get('POSTGREST_EXTERNAL_PORT', '3001')

# PostgREST API configuration
API_CONFIG = {
    'base_url': f'http://localhost:{POSTGREST_PORT}',
    'default_role': 'phisaver',  # Use phisaver role for full access
    'token_expiry_hours': 24
}

console = Console()


def get_jwt_token(role: str = None) -> str:
    """Get a JWT token for API authentication."""
    if role is None:
        role = API_CONFIG['default_role']
    
    try:
        token = generate_jwt_token(role, API_CONFIG['token_expiry_hours'])
        return token
    except Exception as e:
        console.print(f"[red]Error generating JWT token: {e}[/red]")
        sys.exit(1)


def make_api_request(endpoint: str, params: Optional[Dict[str, Any]] = None, token: str = None) -> Optional[List[Dict]]:
    """Make a request to the PostgREST API."""
    if token is None:
        token = get_jwt_token()
    
    url = f"{API_CONFIG['base_url']}/{endpoint}"
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        console.print(f"[red]Error making API request: {e}[/red]")
        if hasattr(e, 'response') and e.response is not None:
            console.print(f"[red]Response: {e.response.text}[/red]")
        return None


def fetch_iotawatt_data(limit: int = 100, token: str = None) -> List[Dict[str, Any]]:
    """Fetch data from the iotawatt table via PostgREST API."""
    params = {
        'order': 'timestamp.desc',
        'limit': limit
    }
    
    data = make_api_request('iotawatt', params, token)
    return data if data is not None else []


def get_table_stats(token: str = None) -> dict:
    """Get statistics about the iotawatt table via PostgREST API."""
    try:
        # Get all data to calculate stats (for small datasets)
        # For large datasets, you'd want to use PostgREST aggregation functions
        all_data = make_api_request('iotawatt', {'select': 'timestamp,device,sensor'}, token)
        
        if not all_data:
            return {}
        
        # Calculate statistics
        timestamps = [datetime.fromisoformat(row['timestamp'].replace('Z', '+00:00')) for row in all_data if row.get('timestamp')]
        devices = {row['device'] for row in all_data if row.get('device')}
        sensors = {row['sensor'] for row in all_data if row.get('sensor')}
        
        return {
            'total_count': len(all_data),
            'min_date': min(timestamps) if timestamps else None,
            'max_date': max(timestamps) if timestamps else None,
            'unique_devices': len(devices),
            'unique_sensors': len(sensors)
        }
    except Exception as e:
        console.print(f"[red]Error fetching stats: {e}[/red]")
        return {}


def create_data_table(data: List[Dict[str, Any]], title: str = "IoTaWatt Data") -> Table:
    """Create a rich table with the iotawatt data."""
    table = Table(
        title=title,
        box=box.ROUNDED,
        title_style="bold blue",
        header_style="bold cyan",
        row_styles=["none", "dim"]
    )
    
    # Add columns
    table.add_column("Timestamp", style="green", width=20)
    table.add_column("Device", style="yellow", width=20)
    table.add_column("Sensor", style="magenta", width=15)
    table.add_column("Power (W)", style="red", justify="right", width=10)
    table.add_column("PF", style="blue", justify="right", width=8)
    table.add_column("Current (A)", style="bright_yellow", justify="right", width=12)
    table.add_column("Voltage (V)", style="bright_magenta", justify="right", width=12)
    
    # Add rows
    for row in data:
        # Extract values from dictionary
        timestamp_str = row.get('timestamp', '')
        device = row.get('device', '')
        sensor = row.get('sensor', '')
        power = row.get('power')
        pf = row.get('pf')
        current = row.get('current')
        voltage = row.get('v')  # Note: voltage field is 'v' in the database
        
        # Format timestamp
        if timestamp_str:
            try:
                # Parse ISO format timestamp from PostgREST
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                ts_str = timestamp.strftime("%Y-%m-%d %H:%M:%S")
            except ValueError:
                ts_str = timestamp_str
        else:
            ts_str = "N/A"
        
        # Format numeric values
        power_str = f"{power:.2f}" if power is not None else "N/A"
        pf_str = f"{pf:.3f}" if pf is not None else "N/A"
        current_str = f"{current:.2f}" if current is not None else "N/A"
        voltage_str = f"{voltage:.1f}" if voltage is not None else "N/A"
        
        table.add_row(
            ts_str,
            str(device) if device else "N/A",
            str(sensor) if sensor else "N/A",
            power_str,
            pf_str,
            current_str,
            voltage_str
        )
    
    return table


def display_stats(stats: dict):
    """Display database statistics."""
    if not stats:
        return
    
    stats_text = Text()
    stats_text.append("📊 Database Statistics\n\n", style="bold blue")
    stats_text.append("Total Records: ", style="bold")
    stats_text.append(f"{stats['total_count']:,}\n", style="green")
    stats_text.append("Unique Devices: ", style="bold")
    stats_text.append(f"{stats['unique_devices']}\n", style="yellow")
    stats_text.append("Unique Sensors: ", style="bold")
    stats_text.append(f"{stats['unique_sensors']}\n", style="magenta")
    
    if stats['min_date'] and stats['max_date']:
        stats_text.append("Date Range: ", style="bold")
        stats_text.append(f"{stats['min_date'].strftime('%Y-%m-%d')} to {stats['max_date'].strftime('%Y-%m-%d')}", style="cyan")
    
    panel = Panel(
        stats_text,
        box=box.ROUNDED,
        padding=(1, 2),
        title="[bold]Database Overview[/bold]",
        title_align="left"
    )
    
    console.print(panel)


def main():
    """Main function to display IoTaWatt data."""
    console.print("\n[bold blue]IoTaWatt PostgREST API Data Viewer (JWT Auth)[/bold blue]\n")
    
    # Show JWT info
    console.print("[dim]Generating JWT token for API access...[/dim]")
    token = get_jwt_token()
    console.print(f"[dim]Using role: {API_CONFIG['default_role']}[/dim]")
    console.print(f"[dim]API endpoint: {API_CONFIG['base_url']}[/dim]")
    console.print(f"[dim]Token generated (expires in {API_CONFIG['token_expiry_hours']} hours)[/dim]\n")
    
    # Display statistics
    console.print("[dim]Fetching database statistics via API...[/dim]")
    stats = get_table_stats(token)
    display_stats(stats)
    console.print()
    
    # Fetch and display data
    console.print("[dim]Fetching latest data via API...[/dim]")
    data = fetch_iotawatt_data(limit=50, token=token)  # Show last 50 records
    
    if data:
        table = create_data_table(data, f"Latest {len(data)} IoTaWatt Records")
        console.print(table)
        console.print(f"\n[dim]Showing {len(data)} most recent records via PostgREST API[/dim]")
    else:
        console.print("[yellow]No data found in the iotawatt table.[/yellow]")
    
    console.print()


if __name__ == "__main__":
    main()