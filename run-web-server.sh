#!/bin/bash

echo "🚀 Starting KROM Crypto Analysis Web Server"
echo "==========================================="
echo ""

# Navigate to the project directory
cd /Users/marcschwyn/Desktop/projects/KROMV12

# Activate virtual environment
source mcp-venv/bin/activate

# Stop any existing MCP server instances
echo "📍 Stopping any existing MCP server instances..."
pkill -f "mcp-server.py" 2>/dev/null

echo "📍 Starting web server..."
echo ""
echo "🌐 Web Interface: http://localhost:5000"
echo "📡 API Endpoints: http://localhost:5000/api/"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run the web server
python web-api-server.py