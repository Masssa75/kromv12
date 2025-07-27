#!/usr/bin/env python3
import http.server
import socketserver
import os

os.chdir('/Users/marcschwyn/Desktop/projects/KROMV12')

PORT = 8000

Handler = http.server.SimpleHTTPRequestHandler

print(f"🚀 Starting server at http://localhost:{PORT}")
print(f"📁 Serving files from: {os.getcwd()}")
print(f"🌐 Open: http://localhost:{PORT}/chat.html")
print("\nPress Ctrl+C to stop")

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    httpd.serve_forever()