#!/bin/bash
# This script runs SQL with environment variables substituted

set -e

# Run the SQL directly with psql and environment variable substitution
PGPASSWORD="$POSTGRES_PASSWORD" psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<EOF
-- Enable TimescaleDB
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create the iotawatt table
CREATE TABLE IF NOT EXISTS public.iotawatt (
  timestamp TIMESTAMPTZ NOT NULL,
  device TEXT NOT NULL,
  sensor TEXT NOT NULL,
  power DOUBLE PRECISION,
  pf DOUBLE PRECISION,
  current DOUBLE PRECISION,
  v DOUBLE PRECISION
);

-- Create Timescale hypertable
SELECT create_hypertable('public.iotawatt', 'timestamp', if_not_exists => TRUE);

-- Create roles securely
-- Anonymous role (read-only access)
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'web_anon') THEN
        CREATE ROLE web_anon NOLOGIN;
    END IF;
END
\$\$;

-- Authenticated user role
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'phisaver') THEN
        CREATE ROLE phisaver NOLOGIN;
    END IF;
END
\$\$;

-- Create authenticator role that can login with environment password
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'authenticator') THEN
        CREATE ROLE authenticator LOGIN PASSWORD '$PGRST_DB_PASSWORD' NOINHERIT;
    END IF;
END
\$\$;

-- Grant role memberships
GRANT web_anon TO authenticator;
GRANT phisaver TO authenticator;

-- Grant access to iotawatt table
GRANT USAGE ON SCHEMA public TO web_anon, phisaver;
GRANT SELECT ON public.iotawatt TO web_anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.iotawatt TO phisaver;

-- Create performance indexes
CREATE INDEX IF NOT EXISTS idx_iotawatt_timestamp ON public.iotawatt (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_iotawatt_device_timestamp ON public.iotawatt (device, timestamp DESC);
EOF
