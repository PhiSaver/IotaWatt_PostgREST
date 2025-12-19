#!/usr/bin/env python3
"""
Upload sample IoTaWatt data to PostgREST API for testing purposes.
"""

from encodings import hz
import os
import requests
from datetime import datetime, timezone
import typer
import random
import logging

from jwtutil import generate_jwt_token


# Configuration from .env file
JWT_SECRET = os.environ.get("PGRST_JWT_SECRET", "").strip()
POSTGREST_PORT = os.environ.get("POSTGREST_EXTERNAL_PORT", "3333")
POSTGREST_HOST = os.environ.get("POSTGREST_HOST", "localhost")
IOTAWATT_TABLE = os.environ.get("IOTAWATT_TABLE", "iotawatt_data")
PG_WRITER_USER = os.environ.get("PG_WRITER_USER", "writer")

app = typer.Typer(help="Upload sample IoTaWatt data to PostgREST")

# Configure logging
console_logger = logging.getLogger("console")
console_logger.addHandler(logging.StreamHandler())  # Also log to console
file_logger = logging.getLogger('file_logger')
file_logger.addHandler(logging.FileHandler('upload.log'))

# Validate configuration
if not JWT_SECRET:
    console_logger.error("Error: PGRST_JWT_SECRET not found in env!")
    raise typer.Exit(1)


def generate_sample_data(num_readings: int = 5, device: str = "hfs02a") -> str:
    """
    Generate sample IoTaWatt readings in CSV format.
    
    Returns CSV string with header and data rows.
    """
    now = datetime.now(timezone.utc).replace(second=0, microsecond=0)  
    
    # CSV header matching PostgREST table columns
    csv_lines = ["timestamp,device,sensor,Watts,Volts,Amps,VA,Wh,PF"]
    
    sensors = ["Net", "Circuit1", "Circuit2", "Circuit3", "Circuit4", "Circuit5", "Circuit6"]
    
    for i in range(num_readings):
        sensor = sensors[i % len(sensors)]
        timestamp = now.isoformat()
        
        # Generate varied electrical measurements
        watts = round(random.uniform(-500, 2000), 1)
        volts = round(random.uniform(235, 245), 1) if i == 0 else None  # Only Net has Volts
        amps = round(watts / 240, 2) if watts != 0 else None
        va = round(abs(watts) * random.uniform(1.0, 1.05), 1) if watts != 0 else None
        pf = round(watts / va, 3) if (va is not None and va != 0) else None
        
        wh = round(abs(watts) * 0.001, 3) if watts != 0 else None
        
        # Format CSV row - use 'NULL' for None values (PostgREST requires uppercase NULL)
        def fmt(val):
            return 'NULL' if val is None else str(val)

        row = f"{timestamp},{device},{sensor},{fmt(watts)},{fmt(volts)},{fmt(amps)},{fmt(va)},{fmt(wh)},{fmt(pf)},{fmt(hz)}"
        csv_lines.append(row)
    
    return "\n".join(csv_lines)


@app.command()
def generate(
    num_readings: int = typer.Option(5, "--count", "-n", help="Number of readings to generate"),
    device: str = typer.Option("hfs02a", "--device", "-d", help="Device name"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """Generate sample CSV data without uploading."""
    if verbose:
        console_logger.setLevel(logging.DEBUG)

    csv_data = generate_sample_data(num_readings, device)
    console_logger.debug(f"Generated CSV Data:\n{csv_data}")
    
    token = generate_jwt_token(PG_WRITER_USER, exp_hours=1)
    console_logger.info(f"Generated JWT Token (1 hr expiry):\n{token}")
    
    # Generate sample data
    csv_data = generate_sample_data(num_readings, device)
    
    # Log the CSV data being uploaded
    console_logger.info(f"Uploading {num_readings} readings for device '{device}' chars: {len(csv_data)}")
    
    
    # PostgREST endpoint
    url = f"http://{POSTGREST_HOST}:{POSTGREST_PORT}/{IOTAWATT_TABLE}"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "text/csv",
        "Prefer": "return=representation",  # Return inserted rows
    }
    
    console_logger.info(f"POST request to: {url}")
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "text/csv",
        "Prefer": "return=representation",  # Return inserted rows
    }
    try:
        response = requests.post(url, data=csv_data, headers=headers)
        file_logger.info(f"\nREQUEST HEADERS\n{headers}")
        file_logger.info(f"\nREQUEST BODY\n({len(csv_data)} chars):\n{csv_data}")
        file_logger.info(f"\nRESPONSE STATUS{response.status_code}")
        file_logger.info(f"\nRESPONSE BODY\n({len(response.text)} chars):\n{response.text}")
        
        if response.status_code in [200, 201]:
            console_logger.info(f"Successfully uploaded {num_readings} readings")
           
        else:
            console_logger.error(f"Upload failed: {response.status_code} - {response.text}")

            raise typer.Exit(1)
            
    except requests.exceptions.RequestException as e:
        console_logger.error(f"Request exception: {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
