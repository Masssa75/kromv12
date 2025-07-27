#!/bin/bash
cd /Users/marcschwyn/Desktop/projects/KROMV12
source mcp-venv/bin/activate
echo "🚀 Starting KROM MCP Server..."
echo "The server will now run and wait for connections from Claude Desktop."
echo "Keep this terminal open while using Claude."
echo ""
python mcp-server.py