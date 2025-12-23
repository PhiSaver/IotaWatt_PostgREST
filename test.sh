#!/bin/bash

JWT_TOKEN_READER=$(uv run jwtutil.py generate reader)
JWT_TOKEN_WRITER=$(uv run jwtutil.py generate writer)
PGRST=http://localhost:$POSTGREST_EXTERNAL_PORT

echo "Using PostgREST endpoint: $PGRST"

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
