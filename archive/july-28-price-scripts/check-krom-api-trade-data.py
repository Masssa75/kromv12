import json
import urllib.request
import os
from datetime import datetime

# Load environment variables
env_vars = {}
with open('.env', 'r') as f:
    for line in f:
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.strip().split('=', 1)
            env_vars[k] = v.strip()

KROM_API_TOKEN = env_vars.get('KROM_API_TOKEN')

if not KROM_API_TOKEN:
    print("Error: KROM_API_TOKEN not found in .env")
    exit(1)

# Fetch latest calls from KROM API
url = "https://krom.one/api/v1/calls?limit=5"

req = urllib.request.Request(url)
req.add_header('Authorization', f'Bearer {KROM_API_TOKEN}')

try:
    response = urllib.request.urlopen(req)
    data = json.loads(response.read().decode())
    
    print(f"Successfully fetched {len(data)} calls from KROM API\n")
    
    for i, call in enumerate(data):
        print(f"\n{'='*60}")
        print(f"Call #{i+1}")
        print(f"{'='*60}")
        
        # Basic info
        print(f"ID: {call.get('id', 'N/A')}")
        print(f"Ticker: {call.get('token', {}).get('symbol', 'N/A')}")
        print(f"Timestamp: {datetime.fromtimestamp(call.get('timestamp', 0))}")
        
        # Check for trade data
        has_trade = 'trade' in call
        print(f"\nHas 'trade' object: {has_trade}")
        
        if has_trade:
            trade = call['trade']
            print(f"Trade data found:")
            print(f"  - buyPrice: ${trade.get('buyPrice', 'N/A')}")
            print(f"  - buyTimestamp: {datetime.fromtimestamp(trade.get('buyTimestamp', 0))}")
            print(f"  - topPrice: ${trade.get('topPrice', 'N/A')}")
            print(f"  - roi: {trade.get('roi', 'N/A')}")
            print(f"  - error: {trade.get('error', 'N/A')}")
        
        # Show all top-level keys
        print(f"\nAll top-level keys in API response:")
        for key in call.keys():
            print(f"  - {key}")
        
        # Show raw JSON for first call
        if i == 0:
            print(f"\nFull JSON for first call:")
            print(json.dumps(call, indent=2))
            
except urllib.error.HTTPError as e:
    print(f"Error fetching from KROM API: {e.code}")
    print(f"Response: {e.read().decode()}")
except Exception as e:
    print(f"Error: {e}")