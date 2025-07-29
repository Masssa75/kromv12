import json
import urllib.request
from datetime import datetime

# Load environment variables
env_vars = {}
with open('.env', 'r') as f:
    for line in f:
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.strip().split('=', 1)
            env_vars[k] = v.strip()

SUPABASE_URL = env_vars['SUPABASE_URL']
SUPABASE_SERVICE_ROLE_KEY = env_vars['SUPABASE_SERVICE_ROLE_KEY']

print("=== Contract Addresses for All 12 Failed Tokens ===")
print(f"Date: {datetime.now()}")

# Get the 20 oldest calls to identify all failed ones
url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
url += "?select=*"
url += "&raw_data->trade->buyPrice=not.is.null"
url += "&raw_data->token->pa=not.is.null"
url += "&order=buy_timestamp.asc"
url += "&limit=20"

req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)

response = urllib.request.urlopen(req)
calls = json.loads(response.read().decode())

# Identify tokens that failed in previous tests (not in successful list)
successful_tokens = ['TCM', 'BIP177', 'CRIPTO', 'PGUSSY', 'ASSOL', 'BUBB']
failed_calls = []

for call in calls:
    raw_data = call['raw_data']
    token = raw_data.get('token', {})
    ticker = token.get('symbol', 'UNKNOWN')
    
    # Skip successful tokens and focus on failed ones
    if ticker not in successful_tokens:
        failed_calls.append(call)

print(f"Found {len(failed_calls)} failed tokens:")
print(f"\n{'#':<3} {'Token':<12} {'Contract Address':<42} {'Network':<10} {'Pool Address':<42}")
print("-" * 115)

# Extract contract addresses for all failed tokens
for i, call in enumerate(failed_calls):
    raw_data = call['raw_data']
    token = raw_data.get('token', {})
    trade = raw_data.get('trade', {})
    
    ticker = token.get('symbol', 'UNKNOWN')
    contract = token.get('ca', 'N/A')
    network = token.get('network', 'unknown')
    pool_address = token.get('pa', 'N/A')
    krom_price = trade.get('buyPrice', 0)
    timestamp = trade.get('buyTimestamp', 0)
    
    print(f"{i+1:<3} {ticker:<12} {contract:<42} {network:<10} {pool_address:<42}")

# Also create a simple list format
print(f"\n" + "="*115)
print(f"\nSIMPLE LIST FORMAT:")
print(f"Contract addresses for the 12 failed tokens:\n")

for i, call in enumerate(failed_calls):
    raw_data = call['raw_data']
    token = raw_data.get('token', {})
    
    ticker = token.get('symbol', 'UNKNOWN')
    contract = token.get('ca', 'N/A')
    network = token.get('network', 'unknown')
    
    print(f"{i+1:2}. {ticker:<12} - {contract} ({network})")

# Create JSON format for easy copying
print(f"\n" + "="*115)
print(f"\nJSON FORMAT:")
json_data = []
for call in failed_calls:
    raw_data = call['raw_data']
    token = raw_data.get('token', {})
    trade = raw_data.get('trade', {})
    
    json_data.append({
        "ticker": token.get('symbol', 'UNKNOWN'),
        "contract": token.get('ca', 'N/A'),
        "network": token.get('network', 'unknown'),
        "pool": token.get('pa', 'N/A'),
        "krom_price": trade.get('buyPrice', 0),
        "timestamp": trade.get('buyTimestamp', 0)
    })

print(json.dumps(json_data, indent=2))