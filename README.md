# IotaWatt PostgREST

A docker container to run a PostgREST -> TimeScaleDB -> Postgres stack for use with IotaWatt. It could be used more generally as there nothing IotaWatt specific. The schema is suited to energy montioring data.

Note this is a _work in progress_ and although it _works on my machine_, you'll likely need to adapt. Feel free to contact me.

## Architecture

This project provides:
- **TimescaleDB**: High-performance time-series database for IoT data storage
- **PostgREST**: Automatic REST API generation from PostgreSQL schema
- **Python Utilities**: Data management and JWT token generation tools

##  Quick Start

1. **Clone and setup**:
   ```bash
   git clone https://github.com/PhiSaver/IotaWatt_PostgREST.git
   cd IotaWatt_PostgREST
   ```

2. **Configure environment**:
   ```bash
   cp .env.template .env
   # Edit .env with your secure passwords and JWT secret
   ```

3. **Start services**:
   ```bash
   make psql_up
   ```

4. **Generate JWT token**:
   ```bash
   make generate_jwt
   ```

See [SETUP.md](SETUP.md) for detailed installation instructions.

##  API Access

Once running, your IoTaWatt data is available via REST API:

```bash
# Get recent data (requires JWT token)
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     "http://localhost:3001/iotawatt?limit=10&order=timestamp.desc"

# Get data for specific device
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     "http://localhost:3001/iotawatt?device=eq.iotawatt-01&limit=50"
```

##  Authentication

Generate tokens with different permissions:
```bash
# Read/write access (24h expiration)
uv run generate_jwt.py generate phisaver 24

# Read-only access (permanent token)
uv run generate_jwt.py generate web_anon --no-expiry
```

## Available Commands

Use `make help` to see all available commands:

```bash
make psql_up        # Start TimescaleDB + PostgREST services
make psql_down      # Stop services and remove volumes
make psql_terminal  # Open PostgreSQL terminal
make generate_jwt   # Generate JWT tokens for API access
make show_db        # Display current IoTaWatt data
```

## Services

- **TimescaleDB**: Runs on port 5433 (customizable via `.env`)
- **PostgREST API**: Runs on port 3001 (customizable via `.env`)

## Development

Original dev environment is linux, VSCode, UV.

```bash
# Install dependencies
uv sync

# Run Python utilities
uv run generate_jwt.py
uv run show_db.py
```
