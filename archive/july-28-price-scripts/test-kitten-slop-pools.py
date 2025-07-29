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

# Get KITTEN and SLOP calls
url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
url += "?select=*"
url += "&ticker=in.(KITTEN,SLOP)"
url += "&raw_data->trade->buyPrice=not.is.null"
url += "&raw_data->token->pa=not.is.null"
url += "&limit=2"

req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)

response = urllib.request.urlopen(req)
calls = json.loads(response.read().decode())

print("=== Testing Tokens with Known Pool Differences ===")
print()

edge_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-single"

for call in calls:
    raw_data = call['raw_data']
    token = raw_data['token']
    trade = raw_data['trade']
    
    ticker = token['symbol']
    krom_price = trade['buyPrice']
    buy_timestamp = trade['buyTimestamp']
    contract = token['ca']
    network = token['network']
    pool_address = token['pa']
    
    print(f"\n{'='*60}")
    print(f"Testing {ticker}")
    print(f"Contract: {contract[:20]}...")
    print(f"Network: {network}")
    print(f"KROM pool: {pool_address[:20]}...")
    print(f"KROM price: ${krom_price:.8f}")
    print(f"Buy time: {datetime.fromtimestamp(buy_timestamp)}")
    
    # Test WITHOUT pool
    print(f"\n1. WITHOUT pool address:")
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
        price_no_pool = result.get('priceAtCall')
        print(f"   Price: ${price_no_pool:.8f}" if price_no_pool else "   Price: None")
        if price_no_pool and krom_price:
            diff = ((price_no_pool - krom_price) / krom_price) * 100
            print(f"   Diff from KROM: {diff:+.2f}%")
    except Exception as e:
        print(f"   Error: {e}")
        price_no_pool = None
    
    # Test WITH pool
    print(f"\n2. WITH KROM's pool address:")
    payload["poolAddress"] = pool_address
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(edge_url, data=data)
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')
    
    try:
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode())
        price_with_pool = result.get('priceAtCall')
        print(f"   Price: ${price_with_pool:.8f}" if price_with_pool else "   Price: None")
        if price_with_pool and krom_price:
            diff = ((price_with_pool - krom_price) / krom_price) * 100
            print(f"   Diff from KROM: {diff:+.2f}%")
            
        # Compare prices
        if price_no_pool and price_with_pool:
            if abs(price_no_pool - price_with_pool) > 0.00000001:
                price_diff = ((price_with_pool - price_no_pool) / price_no_pool) * 100
                print(f"\n   🔄 DIFFERENT PRICES! Pool makes {price_diff:+.2f}% difference")
                print(f"   This confirms the edge function IS using the provided pool")
            else:
                print(f"\n   ⚠️  Same price - might be using same pool")
    except Exception as e:
        print(f"   Error: {e}")

print("\n" + "="*60)
print("\nCONCLUSION:")
print("If we see different prices when providing the pool address,")
print("it confirms the edge function is correctly using the provided pool.")