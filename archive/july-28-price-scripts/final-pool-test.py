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

# Get a fresh SLOP call
url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
url += "?select=*"
url += "&ticker=eq.SLOP"
url += "&raw_data->trade->buyPrice=not.is.null"
url += "&raw_data->token->pa=not.is.null"
url += "&order=buy_timestamp.desc"
url += "&limit=1"

req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)

response = urllib.request.urlopen(req)
calls = json.loads(response.read().decode())

if not calls:
    print("No SLOP call found")
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

print("=== Final Pool Address Test ===")
print(f"Token: {ticker}")
print(f"KROM price: ${krom_price:.8f}")
print(f"Buy time: {datetime.fromtimestamp(buy_timestamp)}")
print(f"KROM pool: {pool_address}")
print()

edge_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-single"

# Test 1: Let edge function auto-select pool
print("1. Edge function AUTO-SELECTING pool:")
payload = {
    "contractAddress": contract,
    "network": network,
    "callTimestamp": buy_timestamp
}

data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(edge_url, data=data)
req.add_header('Content-Type', 'application/json')
req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')

auto_price = None
try:
    response = urllib.request.urlopen(req)
    result = json.loads(response.read().decode())
    auto_price = result.get('priceAtCall')
    print(f"   Price: ${auto_price:.8f}" if auto_price else "   Price: None")
    print(f"   Full result: {json.dumps(result, indent=2)}")
except Exception as e:
    print(f"   Error: {e}")

# Test 2: Provide KROM's pool
print("\n2. Using KROM's pool address:")
payload["poolAddress"] = pool_address

data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(edge_url, data=data)
req.add_header('Content-Type', 'application/json')
req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')

krom_pool_price = None
try:
    response = urllib.request.urlopen(req)
    result = json.loads(response.read().decode())
    krom_pool_price = result.get('priceAtCall')
    print(f"   Price: ${krom_pool_price:.8f}" if krom_pool_price else "   Price: None")
    
    if auto_price and krom_pool_price and auto_price != krom_pool_price:
        diff = ((krom_pool_price - auto_price) / auto_price) * 100
        print(f"   ✅ DIFFERENT PRICE! {diff:+.2f}% difference")
        print(f"   This confirms pool address is being used!")
    elif auto_price and krom_pool_price and auto_price == krom_pool_price:
        print(f"   ⚠️  Same price as auto-selected")
except Exception as e:
    print(f"   Error: {e}")

# Summary
print("\n" + "="*50)
if auto_price and krom_pool_price:
    krom_diff_auto = ((auto_price - krom_price) / krom_price) * 100
    krom_diff_pool = ((krom_pool_price - krom_price) / krom_price) * 100
    
    print(f"KROM price:        ${krom_price:.8f}")
    print(f"Auto-select price: ${auto_price:.8f} ({krom_diff_auto:+.2f}% from KROM)")
    print(f"KROM pool price:   ${krom_pool_price:.8f} ({krom_diff_pool:+.2f}% from KROM)")
    
    if abs(krom_diff_pool) < abs(krom_diff_auto):
        print("\n✅ Using KROM's pool gives MORE ACCURATE price!")
    else:
        print("\n🤔 Auto-selected pool might be more accurate")