#!/bin/bash

echo "🚀 KROM MCP Server Setup Script"
echo "================================"

# Check Python version
echo "📍 Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✅ Python version: $python_version"

# Create virtual environment
echo ""
echo "📍 Creating virtual environment..."
if [ ! -d "mcp-venv" ]; then
    python3 -m venv mcp-venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "📍 Activating virtual environment..."
source mcp-venv/bin/activate

# Install dependencies
echo ""
echo "📍 Installing MCP and dependencies..."
pip install --upgrade pip
pip install mcp aiohttp python-dotenv requests

echo ""
echo "✅ Setup complete!"
echo ""
echo "📋 Next steps:"
echo "1. Copy .env.example to .env and add your API keys"
echo "2. Run the MCP server: python mcp-server.py"
echo "3. Open mcp-dashboard.html in your browser"
echo "4. Configure Claude Desktop to connect to the MCP server"
echo ""
echo "💡 To activate the virtual environment in future sessions:"
echo "   source mcp-venv/bin/activate"