import json
import urllib.request
import os

# Load environment variables
env_vars = {}
with open('.env', 'r') as f:
    for line in f:
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.strip().split('=', 1)
            env_vars[k] = v.strip()

KROM_API_TOKEN = env_vars['KROM_API_TOKEN']

# Test specific IDs
test_ids = [
    ('REMI', '6886d413eb25eec68caf837f'),
    ('SLOP', '6886d2cbeb25eec68caf82f3')
]

print("Testing KROM API directly:\n")

for expected_ticker, krom_id in test_ids:
    print(f"Testing {expected_ticker} (ID: {krom_id}):")
    
    # Try both endpoints
    endpoints = [
        f"https://krom.one/api/v1/calls/{krom_id}",
        f"https://krom.one/api/v1/calls?id={krom_id}"
    ]
    
    for endpoint in endpoints:
        print(f"  Trying: {endpoint}")
        
        req = urllib.request.Request(endpoint)
        req.add_header('Authorization', f'Bearer {KROM_API_TOKEN}')
        
        try:
            response = urllib.request.urlopen(req)
            data = json.loads(response.read().decode())
            
            # Handle array vs object response
            if isinstance(data, list):
                if len(data) > 0:
                    result = data[0]
                    print(f"    ✅ Got array response with {len(data)} items")
                else:
                    print(f"    ❌ Got empty array")
                    continue
            else:
                result = data
                print(f"    ✅ Got object response")
            
            # Check what we got
            actual_id = result.get('_id') or result.get('id')
            actual_ticker = result.get('token', {}).get('symbol', 'N/A')
            
            print(f"    - Response ID: {actual_id}")
            print(f"    - Response ticker: {actual_ticker}")
            print(f"    - ID matches: {actual_id == krom_id}")
            print(f"    - Ticker matches: {actual_ticker == expected_ticker}")
            
            if actual_id != krom_id or actual_ticker != expected_ticker:
                print(f"    ⚠️  WARNING: Data mismatch!")
            
            break  # Don't try second endpoint if first worked
            
        except Exception as e:
            print(f"    ❌ Error: {e}")
    
    print()