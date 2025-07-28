import json
import urllib.request
import urllib.parse
import os
from datetime import datetime

# Load environment variables
env_vars = {}
with open('.env', 'r') as f:
    for line in f:
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.strip().split('=', 1)
            env_vars[k] = v.strip()

KROM_API_TOKEN = env_vars['KROM_API_TOKEN']

print("Exploring KROM API options...\n")

# Test different API endpoints and parameters
tests = [
    {
        'name': 'Latest calls (default)',
        'url': 'https://krom.one/api/v1/calls'
    },
    {
        'name': 'With limit parameter',
        'url': 'https://krom.one/api/v1/calls?limit=5'
    },
    {
        'name': 'With beforeTimestamp (pagination)',
        'url': 'https://krom.one/api/v1/calls?beforeTimestamp=1753670400'  # Around DOGSHIT time
    },
    {
        'name': 'With ticker filter',
        'url': 'https://krom.one/api/v1/calls?ticker=REMI'
    },
    {
        'name': 'With multiple parameters',
        'url': 'https://krom.one/api/v1/calls?limit=100&ticker=REMI'
    }
]

for test in tests:
    print(f"Testing: {test['name']}")
    print(f"URL: {test['url']}")
    
    req = urllib.request.Request(test['url'])
    req.add_header('Authorization', f'Bearer {KROM_API_TOKEN}')
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        
        if isinstance(data, list):
            print(f"✅ Success - Got {len(data)} results")
            if len(data) > 0:
                # Show first result
                first = data[0]
                print(f"   First result: {first.get('token', {}).get('symbol', 'N/A')} (ID: {first.get('_id', 'N/A')})")
                
                # Check if we found specific tokens
                tickers = [item.get('token', {}).get('symbol', 'N/A') for item in data[:5]]
                print(f"   First 5 tickers: {', '.join(tickers)}")
        else:
            print(f"✅ Success - Got object response")
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("\n" + "-"*50 + "\n")

# Also test if there's a search endpoint
print("Looking for other endpoints...")
search_endpoints = [
    'https://krom.one/api/v1/calls/search',
    'https://krom.one/api/v1/search',
    'https://krom.one/api/v1/tokens'
]

for endpoint in search_endpoints:
    req = urllib.request.Request(endpoint)
    req.add_header('Authorization', f'Bearer {KROM_API_TOKEN}')
    
    try:
        response = urllib.request.urlopen(req)
        print(f"✅ {endpoint} exists!")
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"❌ {endpoint} - Not found")
        else:
            print(f"❌ {endpoint} - Error {e.code}")