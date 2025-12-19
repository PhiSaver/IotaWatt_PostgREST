# IotaWatt PostgREST

Works with IoTaWatt energy monitoring, adding uploading to PostgresSQL / TimescaleDB via PostgREST.

## Architecture

This project provides:
- **TimescaleDB Container**: Time-series database for IoTaWatt data
- **PostgREST Container**: Automatic REST API generation from PostgreSQL schema
- **JWT Utilities**: Secure API access with role-based permissions

## Quick Start

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
   make up
   ```

4. **Generate JWT token**:
   ```bash
   make jwt
   export JWT_TOKEN=your_generated_token_here
   ```

##  API Access

Once running, your IoTaWatt data is available via REST API:

```bash

# Get data for specific device
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     "http://localhost:3001/iotawatt?device=eq.iotawatt-01&limit=50"
```

##  Authentication

Three role levels available:
- **anon**: Read-only access to metadata (no actual data)
- **reader**: Read-only access to all data via API and direct DB queries
- **writer**: Read/write access to all data via API

Generate tokens with different permissions:
```bash

# Typical use (permanent writer token for IoTaWatt)
uv run jwt.py generate --role writer iotawatt 
```

##  Available Commands

Use `make help` to see all infrastructure commands.
Use `uv run jwt.py --help` to see JWT generation options.


##  Services

- **TimescaleDB**: Runs on port 5433 (customizable via `.env`)
- **PostgREST API**: Runs on port 3001 (customizable via `.env`)
- **Database**: `phisaver` with `iotawatt` hypertable for time-series data

## Customization

You can customize most names and settings via the `.env` file.

## Basic API Queries

```bash
# Get JWT token
JWT_TOKEN="your_jwt_token_here" 

# Get latest 10 records
curl -H "Authorization: Bearer $JWT_TOKEN" \
     "http://localhost:3000/iotawatt?limit=10&order=timestamp.desc"

# Get data for specific device
curl -H "Authorization: Bearer $JWT_TOKEN" \
     "http://localhost:3000/iotawatt?device=eq.iotawatt-01"
# Get data from last 24 hours
curl -H "Authorization: Bearer $JWT_TOKEN" \
     "http://localhost:3000/iotawatt?timestamp=gte.$(date -d '24 hours ago' -Iseconds)"

# Get aggregated hourly data
curl -H "Authorization: Bearer $JWT_TOKEN" \
     "http://localhost:3000/rpc/hourly_averages"
```

## Data Insertion

```bash
# Insert new IoTaWatt reading
curl -X POST \
     -H "Authorization: Bearer $JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "timestamp": "2024-01-01T12:00:00Z",
       "device": "iotawatt-01", 
       "sensor": "main",
       "Watts": 1500.5,
       "PF": 0.98,
       "Amps": 6.25,
       "Volts": 240.1
     }' \
     "http://localhost:3001/iotawatt"
```
