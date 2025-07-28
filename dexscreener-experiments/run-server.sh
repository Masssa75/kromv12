#!/bin/bash
# Simple script to run the API proxy server

echo "Installing required Python packages..."
pip3 install flask flask-cors requests

echo ""
echo "Starting API Proxy Server..."
echo "Open http://localhost:5002/static in your browser"
echo ""

cd "$(dirname "$0")"
python3 api-proxy-server.py