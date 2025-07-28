#!/usr/bin/env python3
"""
Simple proxy server for DexScreener and GeckoTerminal APIs
Handles CORS and provides a local endpoint for the HTML interface
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
import json

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Base URLs for APIs
DEXSCREENER_BASE = "https://api.dexscreener.com"
GECKOTERMINAL_BASE = "https://api.geckoterminal.com/api/v2"

@app.route('/')
def index():
    return '''
    <h1>API Proxy Server Running</h1>
    <p>Open <a href="http://localhost:5002/static">the explorer</a> to test APIs</p>
    '''

@app.route('/static')
def static_page():
    with open('index.html', 'r') as f:
        return f.read()

# DexScreener endpoints
@app.route('/api/dexscreener/<path:endpoint>')
def dexscreener_proxy(endpoint):
    try:
        # Get query parameters
        params = request.args.to_dict()
        
        # Make request to DexScreener
        url = f"{DEXSCREENER_BASE}/{endpoint}"
        response = requests.get(url, params=params, timeout=10)
        
        return jsonify({
            'success': True,
            'data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            'status_code': response.status_code
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# GeckoTerminal endpoints
@app.route('/api/geckoterminal/<path:endpoint>')
def geckoterminal_proxy(endpoint):
    try:
        # Get query parameters
        params = request.args.to_dict()
        
        # Make request to GeckoTerminal
        url = f"{GECKOTERMINAL_BASE}/{endpoint}"
        response = requests.get(url, params=params, timeout=10)
        
        return jsonify({
            'success': True,
            'data': response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text,
            'status_code': response.status_code
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Test endpoint to check available DexScreener data
@app.route('/api/test/dexscreener')
def test_dexscreener():
    """Test various DexScreener endpoints to see what works"""
    results = {}
    
    # Test endpoints based on common patterns
    test_endpoints = [
        'latest/dex/tokens/trending',
        'latest/dex/pairs/new',
        'latest/dex/search?q=PEPE',
        'latest/dex/tokens/ethereum',
        'orders/v1/solana',  # Try V1 API
        'token-profiles/latest/v1',  # Token profiles
    ]
    
    for endpoint in test_endpoints:
        try:
            url = f"{DEXSCREENER_BASE}/{endpoint}"
            response = requests.get(url, timeout=5)
            results[endpoint] = {
                'status': response.status_code,
                'has_data': bool(response.content),
                'content_type': response.headers.get('content-type', 'unknown')
            }
            if response.status_code == 200:
                try:
                    data = response.json()
                    results[endpoint]['sample'] = str(data)[:200] + '...' if str(data) else 'empty'
                except:
                    results[endpoint]['sample'] = 'not json'
        except Exception as e:
            results[endpoint] = {'error': str(e)}
    
    return jsonify(results)

# Test endpoint for GeckoTerminal
@app.route('/api/test/geckoterminal')
def test_geckoterminal():
    """Test GeckoTerminal endpoints"""
    results = {}
    
    test_endpoints = [
        'networks/trending',
        'networks/ethereum/trending_pools',
        'networks/solana/trending_pools',
        'networks/new_pools',
        'search/pools?query=PEPE',
    ]
    
    for endpoint in test_endpoints:
        try:
            url = f"{GECKOTERMINAL_BASE}/{endpoint}"
            response = requests.get(url, timeout=5)
            results[endpoint] = {
                'status': response.status_code,
                'has_data': bool(response.content)
            }
            if response.status_code == 200:
                try:
                    data = response.json()
                    results[endpoint]['sample'] = str(data)[:200] + '...' if str(data) else 'empty'
                except:
                    results[endpoint]['sample'] = 'not json'
        except Exception as e:
            results[endpoint] = {'error': str(e)}
    
    return jsonify(results)

if __name__ == '__main__':
    print("Starting API Proxy Server...")
    print("Open http://localhost:5002/static in your browser")
    print("Or test endpoints:")
    print("  http://localhost:5002/api/test/dexscreener")
    print("  http://localhost:5002/api/test/geckoterminal")
    app.run(port=5002, debug=True)