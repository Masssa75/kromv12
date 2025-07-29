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
tokens_to_check = [
    ('MIKE', '6886a79deb25eec68caf75de'),
    ('NYAN', '6886a4d9eb25eec68caf74c1'),
    ('SPURDO', '6886a17aeb25eec68caf735d')
]

print("Verifying updated data:\n")

for expected_ticker, krom_id in tokens_to_check:
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls?krom_id=eq.{krom_id}&select=ticker,krom_id,raw_data"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        
        if data:
            entry = data[0]
            raw_data = entry.get('raw_data', {})
            
            actual_ticker = raw_data.get('token', {}).get('symbol', 'N/A')
            
            print(f"{expected_ticker} (ID: {krom_id}):")
            print(f"  - Ticker in raw_data: {actual_ticker}")
            print(f"  - Ticker matches: {'✅' if actual_ticker == expected_ticker else '❌'}")
            
            if 'trade' in raw_data:
                trade = raw_data['trade']
                print(f"  - Buy price: ${trade.get('buyPrice', 'N/A')}")
                print(f"  - ROI: {trade.get('roi', 'N/A')}")
                
                # Also show the call message to verify it's the right call
                message = raw_data.get('text', 'No message')
                if len(message) > 50:
                    message = message[:50] + "..."
                print(f"  - Message: {message}")
            else:
                print(f"  - No trade data")
            print()
            
    except Exception as e:
        print(f"Error checking {expected_ticker}: {e}\n")