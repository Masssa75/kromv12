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

def get_remaining_calls_with_price():
    """Get details of remaining calls with price data"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += f"?select=krom_id,ticker,created_at,price_at_call,current_price,ath_price,price_fetched_at,raw_data"
    url += f"&or=(price_at_call.not.is.null,current_price.not.is.null,ath_price.not.is.null)"
    url += f"&order=created_at.desc"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching calls: {e}")
        return []

print("=== Checking Remaining Records with Price Data ===\n")

remaining = get_remaining_calls_with_price()
print(f"Found {len(remaining)} records with price data:\n")

for i, call in enumerate(remaining):
    print(f"{i+1}. {call.get('ticker', 'Unknown')} (ID: {call.get('krom_id', 'Unknown')})")
    print(f"   Created: {call.get('created_at', 'Unknown')}")
    print(f"   Price at call: {call.get('price_at_call', 'None')}")
    print(f"   Current price: {call.get('current_price', 'None')}")
    print(f"   ATH price: {call.get('ath_price', 'None')}")
    print(f"   Price fetched: {call.get('price_fetched_at', 'None')}")
    
    # Check if it has raw_data
    raw_data = call.get('raw_data')
    if raw_data:
        trade_data = raw_data.get('trade', {})
        if trade_data:
            print(f"   Has trade data: Yes (buyPrice: {trade_data.get('buyPrice', 'N/A')})")
        else:
            print(f"   Has trade data: No")
    print()