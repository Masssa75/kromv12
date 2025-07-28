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

# Get SLOP call
url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
url += "?select=*&ticker=eq.SLOP&raw_data->trade->buyPrice=not.is.null&limit=1"

req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)

response = urllib.request.urlopen(req)
calls = json.loads(response.read().decode())
call = calls[0]

raw_data = call['raw_data']
token = raw_data['token']
trade = raw_data['trade']

buy_timestamp = trade['buyTimestamp']
krom_price = trade['buyPrice']
pool_address = token['pa']

print("=== Timestamp Debug ===")
print(f"KROM buy_timestamp: {buy_timestamp}")
print(f"Converted to datetime: {datetime.fromtimestamp(buy_timestamp)}")
print(f"KROM price: ${krom_price}")
print()

# Call edge function with exact timestamp
edge_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-single"

print("Calling edge function with:")
payload = {
    "contractAddress": token['ca'],
    "network": token['network'],
    "callTimestamp": buy_timestamp,
    "poolAddress": pool_address
}
print(json.dumps(payload, indent=2))

data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(edge_url, data=data)
req.add_header('Content-Type', 'application/json')
req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')

try:
    response = urllib.request.urlopen(req)
    result = json.loads(response.read().decode())
    
    print("\nEdge function response:")
    print(f"callDate in response: {result.get('callDate')}")
    print(f"priceAtCall: ${result.get('priceAtCall')}")
    
    # Check if timestamp conversion is correct
    edge_date = result.get('callDate')
    if edge_date:
        # Parse ISO format
        edge_ts = datetime.fromisoformat(edge_date.replace('Z', '+00:00'))
        print(f"\nTimestamp comparison:")
        print(f"Original: {datetime.fromtimestamp(buy_timestamp)}")
        print(f"Edge fn:  {edge_ts}")
        
except Exception as e:
    print(f"Error: {e}")

# Now let's check what timestamp + 300 gives us (the beforeTimestamp used in OHLCV)
print(f"\nOHLCV query would use beforeTimestamp: {buy_timestamp + 300}")
print(f"Which is: {datetime.fromtimestamp(buy_timestamp + 300)}")