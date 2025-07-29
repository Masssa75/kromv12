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

# Query DOGSHIT
url = f"{SUPABASE_URL}/rest/v1/crypto_calls?ticker=eq.REmi&select=ticker,raw_data"

req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)

try:
    response = urllib.request.urlopen(req)
    data = json.loads(response.read().decode())
    
    if data:
        dogshit = data[0]
        has_trade = 'trade' in dogshit['raw_data'] and dogshit['raw_data']['trade'] is not None
        
        print(f"{dogshit['ticker']} status:")
        print(f"- Has trade data: {has_trade}")
        
        if has_trade:
            trade = dogshit['raw_data']['trade']
            print(f"- Buy price: ${trade.get('buyPrice', 'N/A')}")
            print(f"- Top price: ${trade.get('topPrice', 'N/A')}")
            print(f"- ROI: {trade.get('roi', 'N/A')}")
        else:
            print("- No trade data found")
    else:
        print("Token not found in database")
        
except Exception as e:
    print(f"Error: {e}")