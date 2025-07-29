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

# Get actual DOGSHIT call data
url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
url += "?select=*"
url += "&ticker=eq.DOGSHIT"
url += "&raw_data->trade->buyPrice=not.is.null"
url += "&limit=1"

req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)

response = urllib.request.urlopen(req)
calls = json.loads(response.read().decode())

if not calls:
    print("No DOGSHIT call found")
    exit()

call = calls[0]
raw_data = call['raw_data']
token = raw_data['token']
trade = raw_data['trade']

ticker = token['symbol']
krom_price = trade['buyPrice']
buy_timestamp = trade['buyTimestamp']
contract = token['ca']
network = token['network']
pool_address = token['pa']

print("=== Testing DOGSHIT with Correct Data ===")
print(f"Ticker: {ticker}")
print(f"Contract: {contract[:20]}...")
print(f"Network: {network}")
print(f"KROM pool: {pool_address[:20]}...")
print(f"KROM price: ${krom_price}")
print(f"Buy time: {datetime.fromtimestamp(buy_timestamp)}")
print(f"Timestamp: {buy_timestamp}")
print()

edge_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-single"

# Test 1: Without pool
print("1. WITHOUT pool address:")
payload = {
    "contractAddress": contract,
    "network": network,
    "callTimestamp": buy_timestamp
}

data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(edge_url, data=data)
req.add_header('Content-Type', 'application/json')
req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')

try:
    response = urllib.request.urlopen(req)
    result = json.loads(response.read().decode())
    price = result.get('priceAtCall')
    print(f"   Price: ${price}")
    if price and krom_price:
        diff = ((price - krom_price) / krom_price) * 100
        print(f"   Diff from KROM: {diff:+.2f}%")
except Exception as e:
    print(f"   Error: {e}")

# Test 2: With pool
print("\n2. WITH pool address:")
payload["poolAddress"] = pool_address

data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(edge_url, data=data)
req.add_header('Content-Type', 'application/json')
req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')

try:
    response = urllib.request.urlopen(req)
    result = json.loads(response.read().decode())
    price = result.get('priceAtCall')
    print(f"   Price: ${price}")
    if price and krom_price:
        diff = ((price - krom_price) / krom_price) * 100
        print(f"   Diff from KROM: {diff:+.2f}%")
except Exception as e:
    print(f"   Error: {e}")

# Test 3: With different pool (to force different result)
print("\n3. WITH different pool address (8Pump...HdyfXbbU):")
different_pool = "8PumpHdyfXbbUAGgJ2vn7ekn23jizAKrNH5egH7Gjd4"
payload["poolAddress"] = different_pool

data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(edge_url, data=data)
req.add_header('Content-Type', 'application/json')
req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')

try:
    response = urllib.request.urlopen(req)
    result = json.loads(response.read().decode())
    price = result.get('priceAtCall')
    print(f"   Price: ${price}")
    if price and krom_price:
        diff = ((price - krom_price) / krom_price) * 100
        print(f"   Diff from KROM: {diff:+.2f}%")
except Exception as e:
    print(f"   Error: {e}")