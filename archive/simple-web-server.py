#!/usr/bin/env python3
"""
Simple web server for KROM Crypto Analysis
This serves both the HTML interface and API endpoints
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import json
import asyncio
from urllib.parse import urlparse, parse_qs
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import our crypto server
import importlib.util
spec = importlib.util.spec_from_file_location("mcp_server", "mcp-server.py")
mcp_server = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mcp_server)

# Global crypto server instance
crypto_server = None

async def get_crypto_server():
    global crypto_server
    if crypto_server is None:
        crypto_server = mcp_server.CryptoMCPServer()
        await crypto_server.__aenter__()
    return crypto_server

def run_async(coro):
    """Helper to run async functions"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

class CryptoAPIHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        
        # Serve the main HTML file
        if parsed_path.path == '/':
            self.path = '/crypto-web-interface.html'
            return SimpleHTTPRequestHandler.do_GET(self)
        
        # Handle API endpoints
        if parsed_path.path.startswith('/api/'):
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            try:
                # Price endpoint
                if parsed_path.path.startswith('/api/price/'):
                    symbol = parsed_path.path.split('/')[-1]
                    server = run_async(get_crypto_server())
                    result = run_async(server.get_crypto_price(symbol))
                    self.wfile.write(json.dumps(result).encode())
                
                # Sentiment endpoint
                elif parsed_path.path == '/api/sentiment':
                    server = run_async(get_crypto_server())
                    result = run_async(server.get_market_sentiment())
                    self.wfile.write(json.dumps(result).encode())
                
                # News endpoint
                elif parsed_path.path.startswith('/api/news/'):
                    query = parsed_path.path.split('/')[-1]
                    server = run_async(get_crypto_server())
                    result = run_async(server.get_crypto_news(query))
                    self.wfile.write(json.dumps(result).encode())
                
                # Trending endpoint
                elif parsed_path.path == '/api/trending':
                    server = run_async(get_crypto_server())
                    result = run_async(server.get_trending_cryptos())
                    self.wfile.write(json.dumps(result).encode())
                
                # Portfolio endpoint
                elif parsed_path.path == '/api/portfolio':
                    server = run_async(get_crypto_server())
                    result = run_async(server.check_portfolio())
                    self.wfile.write(json.dumps(result).encode())
                
                else:
                    self.wfile.write(json.dumps({"error": "Unknown endpoint"}).encode())
                    
            except Exception as e:
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            # Serve static files
            return SimpleHTTPRequestHandler.do_GET(self)
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path.startswith('/api/'):
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            try:
                # Compare cryptos
                if self.path == '/api/compare':
                    server = run_async(get_crypto_server())
                    result = run_async(server.compare_cryptos(data['symbols']))
                    self.wfile.write(json.dumps(result).encode())
                
                # Add to portfolio
                elif self.path == '/api/portfolio/add':
                    server = run_async(get_crypto_server())
                    result = run_async(server.add_to_portfolio(
                        data['symbol'], data['quantity'], data['entry_price']
                    ))
                    self.wfile.write(json.dumps(result).encode())
                
                # Position size calculator
                elif self.path == '/api/position-size':
                    server = run_async(get_crypto_server())
                    result = run_async(server.calculate_position_size(
                        data['account_size'], data['risk_percentage'],
                        data['entry_price'], data['stop_loss']
                    ))
                    self.wfile.write(json.dumps(result).encode())
                
                # Analyze KROM call
                elif self.path == '/api/analyze-krom':
                    server = run_async(get_crypto_server())
                    result = run_async(server.analyze_krom_call(
                        data['ticker'], data.get('contract_address')
                    ))
                    self.wfile.write(json.dumps(result).encode())
                    
            except Exception as e:
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_error(404)
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def main():
    PORT = 5000
    
    print("🚀 Starting KROM Crypto Analysis Web Server")
    print(f"📍 Server running at: http://localhost:{PORT}")
    print("📁 Serving from:", os.getcwd())
    print("\nPress Ctrl+C to stop the server\n")
    
    # Create and start server
    httpd = HTTPServer(('localhost', PORT), CryptoAPIHandler)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        httpd.shutdown()

if __name__ == '__main__':
    main()