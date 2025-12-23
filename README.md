# IotaWatt PostgREST

Works with IoTaWatt energy monitoring, adding uploading to PostgresSQL / TimescaleDB via PostgREST.

## Architecture

This project provides:
- **TimescaleDB Container**: Time-series database for IoTaWatt data. Default port **5432**.
- **PostgREST Container**: REST API generation from PostgreSQL schema. Default port **3000**.
- **JWT Utilities**: Secure API access with role-based permissions. `uv run jwtutil.py`


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

4. **Typical use (permanent writer token for IoTaWatt)**:
   ```bash
   uv run jwtutil.py generate writer --no-expiry > iotawatt_jwt_token.txt
   ```


##  Authentication

Two role levels available:
- **reader**: Read-only access to all data via API and direct DB queries
- **writer**: Read/write access to all data via API

Generate tokens with different permissions via `uv run jwtutil.py generate reader # or writer`.

## Basic API

```bash
# Get JWT token
export JWT_TOKEN_READER=$(uv run jwtutil.py generate reader)
export JWT_TOKEN_WRITER=$(uv run jwtutil.py generate writer)
export PGRST=http://localhost:$POSTGREST_EXTERNAL_PORT

# Put some data
http POST $PGRST/iotawatt \
     Authorization:"Bearer $JWT_TOKEN_WRITER" \
     "Content-Type":"application/json" \
       timestamp=$(date +"%Y-%m-%dT%H:%M:%S%z") \
       device=iotawatt-01 \
       sensor=main \
       Watts=1500.5 \
       PF=0.98 \
       Amps=6.25 \
       Volts=240.1
     
# Get latest 10 records
http GET "$PGRST/iotawatt?limit=10&order=timestamp.desc" \
     Authorization:"Bearer $JWT_TOKEN_READER"

# Get data for specific device
http GET      "$PGRST/iotawatt?device=eq.iotawatt-01" \
     Authorization:"Bearer $JWT_TOKEN_READER"

# Get data from last 24 hours
http GET "$PGRST/iotawatt?timestamp=gte.$(date -d '24 hours ago' +"%Y-%m-%dT%H:%M:%S")" \
     Authorization:"Bearer $JWT_TOKEN_READER"
```