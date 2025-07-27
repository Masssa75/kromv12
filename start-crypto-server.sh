#!/bin/bash

echo "🚀 Starting KROM Crypto Analysis Server"
echo "======================================"
echo ""

# Navigate to project directory
cd /Users/marcschwyn/Desktop/projects/KROMV12

# Activate virtual environment
source mcp-venv/bin/activate

# Run the simple web server
python simple-web-server.py