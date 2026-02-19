#!/bin/bash
# setup_tunnels.sh - Initializes a Cloudflare Quick Tunnel for port 8000
# Usage: ./setup_tunnels.sh

echo "Initializing Cloudflare Quick Tunnel for port 8000..."

if ! command -v cloudflared &> /dev/null
then
    echo "cloudflared could not be found. Please install it first."
    echo "Download: https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/install-run/install-threads/"
    exit
fi

# Run tunnel in background and print URL
cloudflared tunnel --url http://127.0.0.1:8000
