import json
import urllib.request
import time
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

def get_recent_calls():
    """Get very recent calls (last 12 hours)"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += "?select=*"
    url += "&raw_data->trade->buyPrice=not.is.null"
    url += "&raw_data->token->pa=not.is.null"
    # Get calls from last 12 hours
    twelve_hours_ago = int((datetime.now().timestamp() - 12*3600))
    url += f"&raw_data->trade->buyTimestamp=gte.{twelve_hours_ago}"
    url += "&order=buy_timestamp.desc"
    url += "&limit=5"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        return data
    except Exception as e:
        print(f"Error: {e}")
        return []

def test_edge_function_debug(contract, network, timestamp, pool_address=None):
    """Test edge function and capture full response"""
    edge_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-single"
    
    payload = {
        "contractAddress": contract,
        "network": network,
        "callTimestamp": timestamp
    }
    
    if pool_address:
        payload["poolAddress"] = pool_address
    
    data = json.dumps(payload).encode('utf-8')
    
    req = urllib.request.Request(edge_url, data=data)
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')
    
    try:
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode())
        return result
    except Exception as e:
        print(f"Error calling edge function: {e}")
        return None

print("=== Testing Recent Calls with Pool Address ===")
print(f"Time: {datetime.now()}")
print()

# Get recent calls
calls = get_recent_calls()
print(f"Found {len(calls)} recent calls (last 12 hours)\n")

if not calls:
    print("No recent calls found. Let's test with specific known calls...")
    # Get DOGSHIT, KITTEN, SLOP specifically
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += "?select=*"
    url += "&raw_data->trade->buyPrice=not.is.null"
    url += "&raw_data->token->pa=not.is.null"
    url += "&ticker=in.(DOGSHIT,KITTEN,SLOP)"
    url += "&limit=3"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    response = urllib.request.urlopen(req)
    calls = json.loads(response.read().decode())

for i, call in enumerate(calls):
    raw_data = call['raw_data']
    token = raw_data['token']
    trade = raw_data['trade']
    
    ticker = token['symbol']
    krom_price = trade['buyPrice']
    buy_timestamp = trade['buyTimestamp']
    contract = token['ca']
    network = token['network']
    pool_address = token['pa']
    
    buy_time = datetime.fromtimestamp(buy_timestamp)
    age_hours = (datetime.now() - buy_time).total_seconds() / 3600
    
    print(f"\n{i+1}. {ticker} - {age_hours:.1f} hours old")
    print(f"   KROM price: ${krom_price:.8f}")
    print(f"   Buy time: {buy_time}")
    print(f"   Contract: {contract[:16]}...")
    print(f"   Pool: {pool_address[:16]}...")
    print(f"   Network: {network}")
    
    # Test WITHOUT pool address
    print(f"\n   Testing WITHOUT pool address:")
    result_no_pool = test_edge_function_debug(contract, network, buy_timestamp)
    if result_no_pool:
        price = result_no_pool.get('priceAtCall')
        if price:
            print(f"   Price: ${price:.8f}")
            diff = ((price - krom_price) / krom_price) * 100
            print(f"   Diff from KROM: {diff:+.2f}%")
    
    time.sleep(1)  # Rate limit
    
    # Test WITH pool address
    print(f"\n   Testing WITH pool address:")
    result_with_pool = test_edge_function_debug(contract, network, buy_timestamp, pool_address)
    if result_with_pool:
        price = result_with_pool.get('priceAtCall')
        if price:
            print(f"   Price: ${price:.8f}")
            diff = ((price - krom_price) / krom_price) * 100
            print(f"   Diff from KROM: {diff:+.2f}%")
            
            # Check if prices are different
            if result_no_pool and result_no_pool.get('priceAtCall'):
                if price != result_no_pool.get('priceAtCall'):
                    print(f"   ✅ Using different pool! Prices differ.")
                else:
                    print(f"   ⚠️  Same price as without pool - may not be using provided pool")
    
    print("-" * 60)
    time.sleep(1)  # Rate limit