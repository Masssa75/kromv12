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

def get_test_call():
    """Get DOGSHIT call which we know works"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += "?select=*"
    url += "&ticker=eq.DOGSHIT"
    url += "&raw_data->trade->buyPrice=not.is.null"
    url += "&limit=1"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        return data[0] if data else None
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_edge_function(contract, network, timestamp, pool_address=None):
    """Test edge function with and without pool address"""
    edge_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-single"
    
    payload = {
        "contractAddress": contract,
        "network": network,
        "callTimestamp": timestamp
    }
    
    if pool_address:
        payload["poolAddress"] = pool_address
    
    data = json.dumps(payload).encode('utf-8')
    
    req = urllib.request.Request(edge_url, data=data, method='POST')
    req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')
    req.add_header('Content-Type', 'application/json')
    
    try:
        response = urllib.request.urlopen(req)
        return json.loads(response.read().decode())
    except Exception as e:
        return {"error": str(e)}

print("=== Testing Edge Function with Pool Address ===")
print(f"Time: {datetime.now()}\n")

# Get test call
call = get_test_call()
if not call:
    print("No test call found!")
    exit()

raw_data = call.get('raw_data', {})
trade = raw_data.get('trade', {})
token = raw_data.get('token', {})

ticker = call.get('ticker')
krom_price = trade.get('buyPrice')
buy_timestamp = trade.get('buyTimestamp')
contract = token.get('ca')
network = token.get('network')
pool_address = token.get('pa')  # KROM's pool address

print(f"Testing {ticker}")
print(f"KROM buy price: ${krom_price:.8f}")
print(f"Buy time: {datetime.fromtimestamp(buy_timestamp)}")
print(f"Contract: {contract[:20]}...")
print(f"KROM pool: {pool_address[:20]}...")

# Test 1: Without pool address (current behavior)
print("\n1. Edge function WITHOUT pool address:")
result1 = test_edge_function(contract, network, buy_timestamp)
if "error" not in result1:
    gecko_price1 = result1.get('priceAtCall')
    used_pool1 = result1.get('poolAddress', 'Unknown')
    if gecko_price1:
        print(f"   Price: ${gecko_price1:.8f}")
    else:
        print(f"   Price: None")
    print(f"   Pool used: {used_pool1[:20] if used_pool1 != 'Unknown' else 'Unknown'}...")
    if gecko_price1 and krom_price:
        diff1 = ((krom_price - gecko_price1) / gecko_price1) * 100
        print(f"   Difference: {diff1:+.1f}%")
else:
    print(f"   Error: {result1['error']}")

# Test 2: With KROM's pool address
print("\n2. Edge function WITH KROM's pool address:")
result2 = test_edge_function(contract, network, buy_timestamp, pool_address)
if "error" not in result2:
    gecko_price2 = result2.get('priceAtCall')
    used_pool2 = result2.get('poolAddress', 'Unknown')
    if gecko_price2:
        print(f"   Price: ${gecko_price2:.8f}")
    else:
        print(f"   Price: None")
    print(f"   Pool used: {used_pool2[:20] if used_pool2 != 'Unknown' else 'Unknown'}...")
    if gecko_price2 and krom_price:
        diff2 = ((krom_price - gecko_price2) / gecko_price2) * 100
        print(f"   Difference: {diff2:+.1f}%")
else:
    print(f"   Error: {result2['error']}")

# Compare pools
print("\n=== Pool Comparison ===")
if 'poolAddress' in result1 and pool_address:
    if result1.get('poolAddress') == pool_address:
        print("✅ Edge function found the same pool as KROM")
    else:
        print("❌ Edge function is using a DIFFERENT pool!")
        print(f"   KROM pool: {pool_address}")
        print(f"   Edge pool: {result1.get('poolAddress')}")

print("\n=== Conclusion ===")
print("If prices match better with KROM's pool address,")
print("we need to update the edge function to accept poolAddress parameter")