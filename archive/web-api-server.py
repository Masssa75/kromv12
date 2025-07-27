#!/usr/bin/env python3
"""
Web API Server for KROM Crypto Analysis
Provides REST API endpoints and serves the web interface
"""

from flask import Flask, jsonify, request, render_template_string, send_from_directory
from flask_cors import CORS
import asyncio
import json
import os
from datetime import datetime
import sys

# Import our MCP server crypto tools
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import importlib.util
spec = importlib.util.spec_from_file_location("mcp_server", "mcp-server.py")
mcp_server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mcp_server)

app = Flask(__name__)
CORS(app)

# Initialize the crypto server
crypto_server = None

async def init_crypto_server():
    """Initialize the crypto server once"""
    global crypto_server
    if crypto_server is None:
        crypto_server = mcp_server.CryptoMCPServer()
        await crypto_server.__aenter__()
    return crypto_server

def run_async(coro):
    """Helper to run async functions in Flask"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

# API Routes
@app.route('/api/price/<symbol>')
def get_price(symbol):
    """Get cryptocurrency price"""
    try:
        server = run_async(init_crypto_server())
        result = run_async(server.get_crypto_price(symbol))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sentiment')
def get_sentiment():
    """Get market sentiment"""
    try:
        server = run_async(init_crypto_server())
        result = run_async(server.get_market_sentiment())
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/news/<query>')
def get_news(query):
    """Get crypto news"""
    try:
        server = run_async(init_crypto_server())
        result = run_async(server.get_crypto_news(query))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/trending')
def get_trending():
    """Get trending cryptocurrencies"""
    try:
        server = run_async(init_crypto_server())
        result = run_async(server.get_trending_cryptos())
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/compare', methods=['POST'])
def compare_cryptos():
    """Compare multiple cryptocurrencies"""
    try:
        symbols = request.json.get('symbols', [])
        server = run_async(init_crypto_server())
        result = run_async(server.compare_cryptos(symbols))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/portfolio/add', methods=['POST'])
def add_to_portfolio():
    """Add to portfolio"""
    try:
        data = request.json
        server = run_async(init_crypto_server())
        result = run_async(server.add_to_portfolio(
            data['symbol'],
            data['quantity'],
            data['entry_price']
        ))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/portfolio')
def check_portfolio():
    """Check portfolio"""
    try:
        server = run_async(init_crypto_server())
        result = run_async(server.check_portfolio())
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/position-size', methods=['POST'])
def calculate_position():
    """Calculate position size"""
    try:
        data = request.json
        server = run_async(init_crypto_server())
        result = run_async(server.calculate_position_size(
            data['account_size'],
            data['risk_percentage'],
            data['entry_price'],
            data['stop_loss']
        ))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/analyze-krom', methods=['POST'])
def analyze_krom():
    """Analyze KROM call"""
    try:
        data = request.json
        server = run_async(init_crypto_server())
        result = run_async(server.analyze_krom_call(
            data['ticker'],
            data.get('contract_address')
        ))
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Serve the main page
@app.route('/')
def index():
    """Serve the main web interface"""
    try:
        with open('crypto-web-interface.html', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return "Error: crypto-web-interface.html not found. Make sure you're running from the KROMV12 directory.", 404

if __name__ == '__main__':
    print("🚀 Starting KROM Crypto Analysis Web Server")
    print("📍 Access the interface at: http://localhost:5000")
    print("📡 API endpoints available at: http://localhost:5000/api/")
    print("\nPress Ctrl+C to stop the server")
    
    # Run the Flask server
    app.run(debug=True, host='0.0.0.0', port=5000)