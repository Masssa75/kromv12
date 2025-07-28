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

# Get the last 6 calls
url = f"{SUPABASE_URL}/rest/v1/crypto_calls?order=created_at.desc&limit=6&select=ticker,krom_id,raw_data"

req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)

print("=== Final Verification of Last 6 Calls ===\n")

try:
    response = urllib.request.urlopen(req)
    calls = json.loads(response.read().decode())
    
    for i, call in enumerate(calls):
        ticker = call['ticker']
        krom_id = call['krom_id']
        raw_data = call.get('raw_data', {})
        
        print(f"{i+1}. {ticker} (ID: {krom_id})")
        
        if raw_data:
            # Check if ticker in raw_data matches
            data_ticker = raw_data.get('token', {}).get('symbol', 'N/A')
            print(f"   Ticker in raw_data: {data_ticker} {'✅' if data_ticker == ticker else '❌ MISMATCH!'}")
            
            # Check trade data
            if 'trade' in raw_data:
                trade = raw_data['trade']
                buy_price = trade.get('buyPrice', 'N/A')
                print(f"   Buy price: ${buy_price}")
                print(f"   ROI: {trade.get('roi', 'N/A')}")
            else:
                print(f"   No trade data")
            
            # Show snippet of message to verify it's the right call
            message = raw_data.get('text', 'No message')
            if len(message) > 60:
                message = message[:60] + "..."
            print(f"   Message: {message}")
        else:
            print(f"   No raw_data")
        
        print()
        
except Exception as e:
    print(f"Error: {e}")