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

SUPABASE_URL = env_vars['SUPABASE_URL']
SUPABASE_SERVICE_ROLE_KEY = env_vars['SUPABASE_SERVICE_ROLE_KEY']

# Query for DOGSHIT and REmi
url = f"{SUPABASE_URL}/rest/v1/crypto_calls?or=(ticker.eq.DOGSHIT,ticker.eq.REmi)&select=ticker,krom_id,raw_data"

req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)

try:
    response = urllib.request.urlopen(req)
    data = json.loads(response.read().decode())
    
    print(f"Found {len(data)} tokens\n")
    
    for token in data:
        ticker = token['ticker']
        krom_id = token['krom_id']
        raw_data = token.get('raw_data', {})
        
        print(f"{ticker} (ID: {krom_id}):")
        print(f"- Has raw_data: {bool(raw_data)}")
        print(f"- raw_data keys: {list(raw_data.keys()) if raw_data else 'None'}")
        print(f"- Has trade object: {'trade' in raw_data}")
        
        if 'trade' in raw_data and raw_data['trade']:
            trade = raw_data['trade']
            print(f"- Buy price: ${trade.get('buyPrice', 'N/A')}")
        else:
            print(f"- No trade data")
        print()
        
except Exception as e:
    print(f"Error: {e}")