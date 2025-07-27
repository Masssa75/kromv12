#!/usr/bin/env python3
"""Simple server for NLP results viewer"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        return super().end_headers()
    
    def do_GET(self):
        # Serve the HTML viewer by default
        if self.path == '/':
            self.path = '/nlp-results-viewer.html'
        return super().do_GET()

if __name__ == '__main__':
    os.chdir('/Users/marcschwyn/Desktop/projects/KROMV12')
    server = HTTPServer(('localhost', 8080), CORSRequestHandler)
    print("NLP Results Viewer running at: http://localhost:8080")
    print("The page will auto-refresh every 10 seconds to show new results")
    print("\nPress Ctrl+C to stop the server")
    server.serve_forever()