# CORS and Server Architecture Solution

## Problem Summary

When attempting to serve both a web interface (HTML/JS) and API endpoints from a single server, we encountered several issues:

1. **CORS (Cross-Origin Resource Sharing) Errors**: Browser security prevented the frontend from calling the backend API
2. **Async/Await Conflicts**: Mixing async Python code with synchronous Flask caused event loop errors
3. **Port Conflicts**: Single server couldn't properly handle both static files and API requests
4. **Complexity**: Trying to make one server do everything led to convoluted code

## Initial Failed Attempts

### Attempt 1: Single Combined Server
```python
# all-in-one-server.py (FAILED)
# Tried to serve HTML and API from same Flask server
# Result: CORS errors, async issues
```

### Attempt 2: Complex CORS Headers
```python
# Tried adding elaborate CORS configurations
# Result: Partial success but unreliable
```

## Final Solution: Two-Server Architecture

### Architecture Overview
```
Browser
  ├── http://localhost:8000 (HTML/JS/CSS)
  │   └── quick-server.py (Simple HTTP Server)
  │
  └── http://localhost:5001/api/* (API Calls)
      └── all-in-one-server.py (Flask API Server)
```

### Server 1: HTML Server (quick-server.py)
**Purpose**: Serve static files only
**Port**: 8000

```python
#!/usr/bin/env python3
import http.server
import socketserver
import os

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

os.chdir(os.path.dirname(os.path.abspath(__file__)))

with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
    print(f"Server running at http://localhost:{PORT}/")
    print(f"Serving files from: {os.getcwd()}")
    httpd.serve_forever()
```

### Server 2: API Server (all-in-one-server.py)
**Purpose**: Handle all API logic and AI interactions
**Port**: 5001

```python
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/api/chat', methods=['POST'])
def chat():
    # API logic here
    pass

if __name__ == '__main__':
    app.run(debug=False, host='127.0.0.1', port=5001)
```

### Frontend Configuration
In your HTML/JavaScript, ensure API calls use the correct port:

```javascript
const API_BASE_URL = 'http://localhost:5001';

async function sendMessage(message) {
    const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            message: message,
            session_id: 'unique-session-id'
        })
    });
    
    return response.json();
}
```

## Key Benefits of This Approach

1. **Separation of Concerns**: Each server has one job and does it well
2. **No CORS Issues**: Flask-CORS handles everything cleanly
3. **No Async Conflicts**: API server can use any async code needed
4. **Easy Development**: Can restart either server independently
5. **Scalable**: Can deploy servers separately in production

## How to Run

Always start both servers:

```bash
# Terminal 1 - Start HTML Server
cd /path/to/project
python quick-server.py

# Terminal 2 - Start API Server
cd /path/to/project
python all-in-one-server.py

# Open browser to http://localhost:8000/chat.html
```

## Common Issues and Solutions

### Issue: "Address already in use"
**Solution**: Kill the process using the port
```bash
# Find process
lsof -i :8000  # or :5001
# Kill it
kill -9 <PID>
```

### Issue: API calls failing
**Solution**: Check both servers are running and ports match in frontend code

### Issue: CORS errors still appearing
**Solution**: Ensure Flask-CORS is installed and initialized:
```bash
pip install flask-cors
```

## Production Considerations

For production deployment:
1. Use proper web servers (nginx for static, gunicorn for Flask)
2. Configure proper CORS origins (not '*')
3. Use environment variables for API URLs
4. Consider using a reverse proxy to serve both from same domain

## Conclusion

The two-server architecture solved all our development issues and provides a clean, maintainable structure for MCP-style applications with web interfaces. This pattern can be reused for any project requiring a web UI with a separate API backend.

---
*Last Updated: May 24, 2025*
*Created during KROMV12 project development*