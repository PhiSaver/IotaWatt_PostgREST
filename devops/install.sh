#!/bin/bash
# Install quadlet files and start IoTaWatt PostgREST services
set -e

# Run in script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

# Ensure .env exists, and load it
if [ ! -f .env ]; then
    echo "ERROR: Missing .env file in directory"
    exit 1
fi

if [ ! -f init_db.sh ]; then
    echo "ERROR: Missing init_db.sh file in directory"
    exit 1
fi

set -a
source .env
set +a

echo Running in $SCRIPT_DIR

# Check if network exists, create if needed
if ! podman network exists iotawatt 2>/dev/null; then
    echo "Creating iotawatt network..."
    podman network create iotawatt
else
    echo "Network iotawatt already exists"
fi

# Install quadlet files to systemd, rendering .templates with envsubst
echo "Rendering quadlet files to systemd..."
SYSTEMD_QUADLET_DIR="$HOME/.config/containers/systemd"
mkdir -p "$SYSTEMD_QUADLET_DIR"

# Render templates into systemd directory
templates=("./quadlets"/*.template)
for tmpl in "${templates[@]}"; do
    out="$SYSTEMD_QUADLET_DIR/$(basename "$tmpl" .template)"
    rm -f "$out"
    #echo "Rendering $(readlink -f "$tmpl") -> $out"
    envsubst < "$tmpl" > "$out"
done

# Copy any non-template quadlet files (volume, network)
find ./quadlets -maxdepth 1 -type f ! -name '*.template' | while read -r f; do
    out="$SYSTEMD_QUADLET_DIR/$(basename "$f")"
    #echo "Copying $(readlink -f "$f") -> $out"
    cp "$f" "$out"
done

# Reload systemd to pick up new files
echo "Reloading systemd..."
systemctl --user daemon-reload

# Restart container services
echo "Restarting container services..."
systemctl --user restart timescale.service postgrest.service

# Wait a moment and check status
sleep 1
echo "Deployment complete!"
echo "To enable services on boot: loginctl enable-linger $USER"
echo "Connect to PostgREST API at http://localhost:$POSTGREST_EXTERNAL_PORT"
