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

def get_test_calls():
    """Get various test calls with different ages"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += "?select=*"
    url += "&raw_data->trade->buyPrice=not.is.null"
    url += "&raw_data->token->pa=not.is.null"
    url += "&order=buy_timestamp.desc"
    url += "&limit=10"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        return data
    except Exception as e:
        print(f"Error: {e}")
        return []

def test_edge_function(contract, network, timestamp, pool_address=None):
    """Test edge function with pool address"""
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
        return result.get('priceAtCall')
    except Exception as e:
        print(f"Error calling edge function: {e}")
        return None

def get_ohlcv_direct(network, pool_address, timestamp):
    """Get OHLCV data directly from GeckoTerminal"""
    base_url = "https://api.geckoterminal.com/api/v2"
    before_timestamp = timestamp + 300  # 5 minutes after
    
    url = f"{base_url}/networks/{network}/pools/{pool_address}/ohlcv/minute"
    url += f"?before_timestamp={before_timestamp}&limit=10&currency=usd"
    
    req = urllib.request.Request(url)
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        ohlcv_list = data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
        
        # Find the closest candle
        for candle in ohlcv_list:
            candle_time = candle[0]
            if abs(candle_time - timestamp) <= 60:  # Within 1 minute
                return {
                    'timestamp': candle_time,
                    'open': candle[1],
                    'high': candle[2],
                    'low': candle[3],
                    'close': candle[4],
                    'volume': candle[5]
                }
        return None
    except Exception as e:
        print(f"Error fetching OHLCV: {e}")
        return None

print("=== Testing Edge Function Accuracy with Pool Address ===")
print(f"Time: {datetime.now()}")
print()

# Get test calls
calls = get_test_calls()
print(f"Found {len(calls)} calls with trade data and pool addresses\n")

# Test different age ranges
results = []
for i, call in enumerate(calls[:5]):  # Test first 5
    raw_data = call['raw_data']
    token = raw_data['token']
    trade = raw_data['trade']
    
    ticker = token['symbol']
    krom_price = trade['buyPrice']
    buy_timestamp = trade['buyTimestamp']
    contract = token['ca']
    network = token['network']
    pool_address = token['pa']
    
    # Calculate age
    buy_time = datetime.fromtimestamp(buy_timestamp)
    age_hours = (datetime.now() - buy_time).total_seconds() / 3600
    
    print(f"\n{i+1}. {ticker} - {age_hours:.1f} hours old")
    print(f"   KROM price: ${krom_price:.8f}")
    print(f"   Buy time: {buy_time}")
    print(f"   Pool: {pool_address[:10]}...")
    
    # Test edge function WITHOUT pool address
    edge_price_no_pool = test_edge_function(contract, network, buy_timestamp)
    
    # Test edge function WITH pool address
    edge_price_with_pool = test_edge_function(contract, network, buy_timestamp, pool_address)
    
    # Get OHLCV data directly
    ohlcv = get_ohlcv_direct(network, pool_address, buy_timestamp)
    
    print(f"\n   Results:")
    print(f"   Edge (no pool):   ${edge_price_no_pool:.8f}" if edge_price_no_pool else "   Edge (no pool):   None")
    print(f"   Edge (with pool): ${edge_price_with_pool:.8f}" if edge_price_with_pool else "   Edge (with pool): None")
    
    if ohlcv:
        print(f"\n   Direct OHLCV from pool {pool_address[:10]}...:")
        print(f"   Open:  ${ohlcv['open']:.8f}")
        print(f"   High:  ${ohlcv['high']:.8f}")
        print(f"   Low:   ${ohlcv['low']:.8f}")
        print(f"   Close: ${ohlcv['close']:.8f} ← Edge function returns this")
        print(f"   Time diff: {abs(ohlcv['timestamp'] - buy_timestamp)} seconds")
    
    # Calculate differences
    if edge_price_with_pool and krom_price:
        diff_pct = ((edge_price_with_pool - krom_price) / krom_price) * 100
        print(f"\n   Difference (Edge w/pool vs KROM): {diff_pct:+.2f}%")
        
        if ohlcv:
            # Check if KROM price is within OHLCV range
            in_range = ohlcv['low'] <= krom_price <= ohlcv['high']
            print(f"   KROM price within OHLCV range: {'✅ YES' if in_range else '❌ NO'}")
            
            # Check if edge price matches close
            close_match = abs(edge_price_with_pool - ohlcv['close']) < 0.00000001
            print(f"   Edge returns close price: {'✅ YES' if close_match else '❌ NO'}")
    
    time.sleep(0.5)  # Rate limiting

print("\n=== Summary ===")
print("The edge function returns the CLOSE price of the minute candle")
print("When provided with KROM's pool address, prices should match accurately")