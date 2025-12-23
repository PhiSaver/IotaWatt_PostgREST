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
5. **Test API**:
   ```bash
   cat ./test.sh # View test script for API usage
   ./test.sh  
   ```


##  Authentication

Two role levels available:
- **reader**: Read-only access to all data via API and direct DB queries
- **writer**: Read/write access to all data via API

Generate tokens with different permissions via `uv run jwtutil.py generate reader # or writer`.

## Deployment

There are two deployment options:

### Docker/Podman Compose

Runs a podman or docker compose setup locally. Based on the `compose.yml`. Good for development and testing.
Use the following commands:
` make up` to start, `make down` to stop.

### Systemd Quadlets 

Deploys the services as systemd user services using Podman and Quadlets. Suitable for production use. Check .env for configuration.
Use the following commands:
`make deploy-local` to deploy on the local machine.
`make deploy-remote` to deploy to a remote host via SSH.
