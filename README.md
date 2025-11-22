# IotaWatt PostgREST

A docker container to run a PostgREST -> TimeScaleDB -> Postgres stack for use with IotaWatt. It could be used more generally as there nothing IotaWatt specific. The schema is suited to energy montioring data.

Note this is a _work in progress_ and although it "works on my machine", it's not tested.

## 🏗️ Architecture

This project provides:
- **TimescaleDB**: High-performance time-series database for IoT data storage
- **PostgREST**: Automatic REST API generation from PostgreSQL schema
- **JWT Authentication**: Secure API access with role-based permissions
- **Python Utilities**: Data management and JWT token generation tools

## 🚀 Quick Start

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

## 📊 API Access

Once running, your IoTaWatt data is available via REST API:

```bash
# Get recent data (requires JWT token)
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     "http://localhost:3001/iotawatt?limit=10&order=timestamp.desc"

# Get data for specific device
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     "http://localhost:3001/iotawatt?device=eq.iotawatt-01&limit=50"
```

## 🔐 Authentication

Two role levels available:
- **web_anon**: Read-only access to IoTaWatt data
- **phisaver**: Full CRUD access to all data

Generate tokens with different permissions:
```bash
# Read/write access (24h expiration)
uv run generate_jwt.py generate phisaver 24

# Read-only access (permanent token)
uv run generate_jwt.py generate web_anon --no-expiry
```

## 🛠️ Available Commands

Use `make help` to see all available commands:

```bash
make psql_up        # Start TimescaleDB + PostgREST services
make psql_down      # Stop services and remove volumes
make psql_terminal  # Open PostgreSQL terminal
make generate_jwt   # Generate JWT tokens for API access
make show_db        # Display current IoTaWatt data
```

## 🐳 Services

- **TimescaleDB**: Runs on port 5433 (customizable via `.env`)
- **PostgREST API**: Runs on port 3001 (customizable via `.env`)
- **Database**: `phisaver` with `iotawatt` hypertable for time-series data

## 📁 Project Structure

```
├── docker-compose.yml    # Container orchestration
├── init_db.sh           # Database initialization script
├── generate_jwt.py      # JWT token generator utility
├── show_db.py          # Database viewing utility  
├── Makefile            # Development commands
├── .env.template       # Environment configuration template
└── pyproject.toml      # Python dependencies (uv/pip)
```

## 🔧 Development

This project uses [uv](https://docs.astral.sh/uv/) for fast Python package management:

```bash
# Install dependencies
uv sync

# Run Python utilities
uv run generate_jwt.py
uv run show_db.py
```

## 🏢 Production Deployment

For production deployment:
1. Use strong passwords and JWT secrets
2. Enable SSL/TLS for API access
3. Configure firewall rules for ports 5433/3001
4. Set up regular database backups
5. Use systemd for service management

See [SETUP.md](SETUP.md) for detailed production deployment instructions.

## 📜 License

This project is part of the PhiSaver IoT monitoring ecosystem.
