# IotaWatt PostgREST Setup Guide

This guide provides step-by-step instructions for setting up the IotaWatt PostgREST monitoring system.

## 📋 Prerequisites

### Required Software

- **Docker** (20.10+) or **Podman** (4.0+)
- **Docker Compose** (v2.0+) or **Podman Compose**
- **Python** (3.12+) - for utilities
- **uv** (recommended) or **pip** - for Python package management

### System Requirements

- **RAM**: Minimum 2GB, recommended 4GB+
- **Storage**: 10GB+ for database and logs
- **Network**: Ports 3001 (PostgREST) and 5433 (PostgreSQL) available

## 🚀 Installation Steps

### 1. Clone Repository

```bash
git clone https://github.com/PhiSaver/IotaWatt_PostgREST.git
cd IotaWatt_PostgREST
```

### 2. Install Python Package Manager (uv)

```bash
# On Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or using pip
pip install uv
```

### 3. Configure Environment Variables

```bash
# Copy template and edit with your values
cp .env.template .env

# Generate secure passwords and JWT secret
echo "POSTGRES_PASSWORD=$(openssl rand -base64 16)" >> .env.local
echo "PGRST_DB_PASSWORD=$(openssl rand -base64 16)" >> .env.local  
echo "PGRST_JWT_SECRET=$(openssl rand -base64 32)" >> .env.local

# Edit .env with your secure values
nano .env  # or vim/code .env
```

**Required .env Configuration:**

```bash
# Database Configuration
POSTGRES_USER=phisaver_user
POSTGRES_PASSWORD=your_secure_password_16_chars_min
POSTGRES_DB=phisaver

# PostgREST Configuration  
PGRST_DB_SCHEMA=public
PGRST_DB_ANON_ROLE=web_anon
PGRST_JWT_SECRET=your_jwt_secret_32_chars_minimum_security
PGRST_ROLE_CLAIM_KEY=.role

# Service Ports
POSTGRES_EXTERNAL_PORT=5433
POSTGREST_EXTERNAL_PORT=3001
```

### 4. Install Python Dependencies

```bash
# Using uv (recommended - fast!)
uv sync

```

### 5. Start Services

```bash
# Start TimescaleDB + PostgREST
make psql_up

# Or manually with docker compose
docker compose up -d --build
```

**Service Startup Verification:**

```bash
# Check container status
docker compose ps

# Check logs if needed
docker compose logs db
docker compose logs postgrest
```

### 6. Generate JWT Token

```bash
# Generate token for full access (24h expiration)
make generate_jwt

# Or generate manually
uv run generate_jwt.py generate phisaver 24

# For permanent read-only access
uv run generate_jwt.py generate web_anon --no-expiry
```

## 🔧 Configuration Options

### Port Configuration

Default ports can be changed in `.env`:

```bash
# Change PostgreSQL port (default: 5433)
POSTGRES_EXTERNAL_PORT=5432

# Change PostgREST API port (default: 3001) 
POSTGREST_EXTERNAL_PORT=3000
```

### Database Schema

The system creates:

- **Database**: `phisaver`
- **Table**: `iotawatt` (TimescaleDB hypertable)
- **Roles**: `web_anon` (read-only), `phisaver` (full access)
- **Indexes**: Optimized for time-series queries

### JWT Configuration

JWT tokens support two roles:

```bash
# Read-only access
uv run generate_jwt.py generate web_anon --no-expiry

# Full CRUD access  
uv run generate_jwt.py generate phisaver 168  # 1 week expiration
```

## 🧪 Testing Installation

### 1. Database Connection Test

```bash
# Connect to PostgreSQL directly
make psql_terminal

# Or manually
docker exec -it timescale-db psql -U phisaver_user -d phisaver
```

### 2. API Endpoint Test

```bash
# Test without authentication (should fail)
curl http://localhost:3001/iotawatt

# Test with JWT token
JWT_TOKEN=$(uv run generate_jwt.py generate web_anon --no-expiry | tail -n1)
curl -H "Authorization: Bearer $JWT_TOKEN" \
     "http://localhost:3001/iotawatt?limit=5"
```

### 3. Insert Test Data

```bash
# View current data
make show_db

# Insert sample data (if available)
make insert_fake
```

## 📊 Usage Examples

### Basic API Queries

```bash
# Get JWT token
JWT_TOKEN="your_jwt_token_here"

# Get latest 10 records
curl -H "Authorization: Bearer $JWT_TOKEN" \
     "http://localhost:3001/iotawatt?limit=10&order=timestamp.desc"

# Get data for specific device
curl -H "Authorization: Bearer $JWT_TOKEN" \
     "http://localhost:3001/iotawatt?device=eq.iotawatt-01"

# Get data from last 24 hours
curl -H "Authorization: Bearer $JWT_TOKEN" \
     "http://localhost:3001/iotawatt?timestamp=gte.$(date -d '24 hours ago' -Iseconds)"

# Get aggregated hourly data
curl -H "Authorization: Bearer $JWT_TOKEN" \
     "http://localhost:3001/rpc/hourly_averages"
```

### Data Insertion

```bash
# Insert new IoTaWatt reading
curl -X POST \
     -H "Authorization: Bearer $JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "timestamp": "2024-01-01T12:00:00Z",
       "device": "iotawatt-01", 
       "sensor": "main",
       "power": 1500.5,
       "pf": 0.98,
       "current": 6.25,
       "v": 240.1
     }' \
     "http://localhost:3001/iotawatt"
```

## 🏗️ Development Commands

All available commands via Makefile:

```bash
make help              # Show all available commands

# Docker/Service Management
make psql_up          # Start services
make psql_down        # Stop services and remove volumes
make docker_prune     # Clean up Docker resources

# Database Operations  
make psql_terminal    # Open PostgreSQL terminal
make show_db          # Display current IoTaWatt data

# JWT Management
make generate_jwt     # Generate JWT token (phisaver role, no expiry)
make jwt_help         # Show JWT generator help

# Testing/Development
make insert_fake      # Insert fake test data
```

### Manual Python Commands

```bash
# JWT token management
uv run generate_jwt.py roles                    # List available roles
uv run generate_jwt.py generate phisaver 24     # Generate 24h token
uv run generate_jwt.py decode TOKEN_HERE        # Decode token info

# Database utilities
uv run show_db.py                               # Show current data
```

## 🚨 Troubleshooting

### Common Issues

**1. Port Conflicts**

```bash
# Check if ports are in use
sudo netstat -tulpn | grep -E ':(3001|5433)'

# Change ports in .env if needed
POSTGRES_EXTERNAL_PORT=5434
POSTGREST_EXTERNAL_PORT=3002
```

**2. Database Connection Failed**

```bash
# Check container logs
docker compose logs db

# Verify environment variables
docker compose config

# Reset database (removes all data)
make psql_down
make psql_up
```

**3. JWT Authentication Failed**

```bash
# Verify JWT secret matches in .env
grep PGRST_JWT_SECRET .env

# Generate new token
uv run generate_jwt.py generate phisaver --no-expiry

# Test token validity
uv run generate_jwt.py decode YOUR_TOKEN
```

**4. PostgREST API Not Responding**

```bash
# Check PostgREST logs
docker compose logs postgrest

# Verify database schema
make psql_terminal
\dt  # List tables
\du  # List roles
```

### Log Analysis

```bash
# View all service logs
docker compose logs -f

# View specific service logs
docker compose logs -f db
docker compose logs -f postgrest

# Check container health
docker compose ps
```

### Reset Everything

```bash
# Complete reset (removes all data)
make psql_down
docker volume prune -f
make psql_up
```

## 🔒 Security Considerations

### Production Deployment

1. **Use Strong Passwords**:
   ```bash
   # Generate secure passwords
   openssl rand -base64 16  # For database passwords
   openssl rand -base64 32  # For JWT secret
   ```

2. **Enable SSL/TLS**:
   - Configure reverse proxy (nginx/traefik) with SSL certificates
   - Use HTTPS for all API endpoints
   - Enable PostgreSQL SSL connections

3. **Network Security**:
   ```bash
   # Configure firewall (example for ufw)
   sudo ufw allow 22/tcp      # SSH only
   sudo ufw allow 443/tcp     # HTTPS only
   sudo ufw deny 3001/tcp     # Block direct PostgREST access
   sudo ufw deny 5433/tcp     # Block direct PostgreSQL access
   ```

4. **Environment Protection**:
   ```bash
   # Secure .env file permissions
   chmod 600 .env
   
   # Don't commit .env to version control
   echo ".env" >> .gitignore
   ```

### JWT Token Security

- **Short-lived tokens**: Use 24-hour expiration for production
- **Role-based access**: Use `web_anon` for read-only clients
- **Token rotation**: Regularly generate new JWT secrets
- **Secure transmission**: Only send tokens over HTTPS

## 📈 Performance Tuning

### Database Optimization

```sql
-- Connect to database
make psql_terminal

-- Check table size and performance
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats 
WHERE tablename = 'iotawatt';

-- Analyze query performance
EXPLAIN ANALYZE 
SELECT * FROM iotawatt 
WHERE timestamp > NOW() - INTERVAL '24 hours'
ORDER BY timestamp DESC 
LIMIT 100;
```

### Scaling Considerations

- **TimescaleDB partitioning**: Automatic time-based partitioning
- **Connection pooling**: Add pgbouncer for high-concurrency scenarios  
- **Read replicas**: Scale read operations with PostgreSQL replication
- **Caching**: Add Redis for frequently accessed data

## 🏢 Production Deployment with systemd

### 1. Create systemd service

```bash
sudo tee /etc/systemd/system/iotawatt-postgrest.service > /dev/null <<EOF
[Unit]
Description=IotaWatt PostgREST Services
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/iotawatt-postgrest
ExecStart=/usr/local/bin/docker-compose up -d
ExecStop=/usr/local/bin/docker-compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF
```

### 2. Deploy and enable

```bash
# Copy project to production location
sudo cp -r . /opt/iotawatt-postgrest/
sudo chown -R root:root /opt/iotawatt-postgrest/
sudo chmod 600 /opt/iotawatt-postgrest/.env

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable iotawatt-postgrest.service
sudo systemctl start iotawatt-postgrest.service

# Check status
sudo systemctl status iotawatt-postgrest.service
```

### 3. Setup log rotation

```bash
sudo tee /etc/logrotate.d/iotawatt-postgrest > /dev/null <<EOF
/opt/iotawatt-postgrest/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0644 root root
}
EOF
```

## 📚 Additional Resources

- **TimescaleDB Documentation**: https://docs.timescale.com/
- **PostgREST API Reference**: https://postgrest.org/en/stable/api.html
- **JWT.io**: https://jwt.io/ - JWT token debugging
- **Docker Compose Reference**: https://docs.docker.com/compose/

## 🆘 Support

For issues and questions:

1. Check the [troubleshooting section](#-troubleshooting)
2. Review container logs: `docker compose logs`
3. Consult the TODO.md for known issues
4. Open an issue on the GitHub repository

---

**Next Steps**: Once setup is complete, see [README.md](README.md) for usage examples and API documentation.
