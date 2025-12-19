#!/bin/bash
# This script runs SQL with environment variables substituted

set -e

# Run the SQL directly with psql and environment variable substitution
PGPASSWORD="$POSTGRES_PASSWORD" psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<EOF
-- Enable TimescaleDB
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Create the $IOTAWATT_TABLE table
    CREATE TABLE IF NOT EXISTS $IOTAWATT_SCHEMA.$IOTAWATT_TABLE (
    timestamp TIMESTAMPTZ NOT NULL,
    device TEXT NOT NULL,
    sensor TEXT NOT NULL,
    "Watts" DOUBLE PRECISION,
    "Volts" DOUBLE PRECISION,
    "Amps" DOUBLE PRECISION,
    "VA" DOUBLE PRECISION,
    "Wh" DOUBLE PRECISION,
    "PF" DOUBLE PRECISION,
    "Hz" DOUBLE PRECISION,
    "VAR" DOUBLE PRECISION,
    "VARh" DOUBLE PRECISION
    );

-- Create Timescale hypertable
SELECT create_hypertable('$IOTAWATT_SCHEMA.$IOTAWATT_TABLE', 'timestamp', if_not_exists => TRUE);

-- Reader has read-only access direct to SQL AND via PostgREST
-- Typically we write to DB via PostgREST using the writer role
-- read from SQL directly using the reader role
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$PG_READER_USER') THEN
        CREATE ROLE $PG_READER_USER LOGIN PASSWORD '$PG_READER_PASSWORD' NOINHERIT;
    END IF;
END
\$\$;

-- Writer has read and write access via PostgREST
-- but cannot login directly to SQL
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$PG_WRITER_USER') THEN
        CREATE ROLE $PG_WRITER_USER NOLOGIN;
    END IF;
END
\$\$;

-- Create authenticator role that can login 
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$PGRST_DB_USER') THEN
        CREATE ROLE $PGRST_DB_USER LOGIN PASSWORD '$PGRST_DB_PASSWORD' NOINHERIT;
    END IF;
END
\$\$;

-- Grant role memberships to allow PostgREST to assume reader and writer roles
GRANT $PG_WRITER_USER TO $PGRST_DB_USER;
GRANT $PG_READER_USER TO $PGRST_DB_USER;


-- Grant access to iotawatt table
GRANT USAGE ON SCHEMA $IOTAWATT_SCHEMA TO $PG_READER_USER, $PG_WRITER_USER;
GRANT SELECT ON $IOTAWATT_SCHEMA.$IOTAWATT_TABLE TO $PG_READER_USER;
GRANT SELECT, INSERT, UPDATE, DELETE ON $IOTAWATT_SCHEMA.$IOTAWATT_TABLE TO $PG_WRITER_USER;


-- Create performance indexes
CREATE INDEX IF NOT EXISTS idx_iotawatt_timestamp ON $IOTAWATT_SCHEMA.$IOTAWATT_TABLE (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_iotawatt_device_timestamp ON $IOTAWATT_SCHEMA.$IOTAWATT_TABLE (device, timestamp DESC);
EOF