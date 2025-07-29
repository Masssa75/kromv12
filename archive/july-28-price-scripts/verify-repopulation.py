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

# Check the updated tokens
tokens = ['REMI', 'SLOP', 'QUOKKA', 'SPURDO']

print("Verifying repopulated data:\n")

for token in tokens:
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls?ticker=eq.{token}&select=ticker,krom_id,raw_data&order=created_at.desc&limit=1"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        
        if data:
            entry = data[0]
            raw_data = entry.get('raw_data', {})
            
            print(f"{token} (ID: {entry['krom_id']}):")
            
            if raw_data and 'trade' in raw_data:
                trade = raw_data['trade']
                print(f"  ✅ Has trade data")
                print(f"  - Buy price: ${trade.get('buyPrice', 'N/A')}")
                print(f"  - Token CA: {raw_data.get('token', {}).get('ca', 'N/A')}")
                print(f"  - Token symbol in data: {raw_data.get('token', {}).get('symbol', 'N/A')}")
            else:
                print(f"  ❌ No trade data found")
            print()
            
    except Exception as e:
        print(f"Error checking {token}: {e}\n")