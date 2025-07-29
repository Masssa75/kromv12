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

def get_direct_ohlcv(network, pool_address, timestamp):
    """Get OHLCV data directly from GeckoTerminal API"""
    base_url = "https://api.geckoterminal.com/api/v2"
    
    # Try minute candles first
    before_timestamp = timestamp + 300  # 5 minutes after
    url = f"{base_url}/networks/{network}/pools/{pool_address}/ohlcv/minute"
    url += f"?before_timestamp={before_timestamp}&limit=10&currency=usd"
    
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0')
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        ohlcv_list = data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
        
        if ohlcv_list:
            # Find closest candle
            for candle in ohlcv_list:
                candle_time = candle[0]
                if abs(candle_time - timestamp) <= 60:  # Within 1 minute
                    return {
                        'open': candle[1],
                        'high': candle[2],
                        'low': candle[3],
                        'close': candle[4],
                        'volume': candle[5],
                        'timestamp': candle_time
                    }
        return None
    except Exception as e:
        return {'error': str(e)}

def test_edge_function(contract, network, timestamp, pool_address):
    """Call edge function"""
    edge_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-single"
    
    payload = {
        "contractAddress": contract,
        "network": network,
        "callTimestamp": timestamp,
        "poolAddress": pool_address
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(edge_url, data=data)
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')
    
    try:
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode())
        return result.get('priceAtCall')
    except:
        return None

print("=== Direct API vs Edge Function Comparison ===")
print(f"Date: {datetime.now()}")
print()

# Get 5 recent calls with different tokens
url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
url += "?select=*"
url += "&raw_data->trade->buyPrice=not.is.null"
url += "&raw_data->token->pa=not.is.null"
url += "&order=buy_timestamp.desc"
url += "&limit=5"

req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)

response = urllib.request.urlopen(req)
calls = json.loads(response.read().decode())

print(f"Testing {len(calls)} recent calls\n")
print(f"{'Token':<10} {'KROM Price':<15} {'Edge Price':<15} {'Direct API':<15} {'Edge vs KROM':<15} {'Direct vs KROM'}")
print("-" * 90)

for call in calls:
    raw_data = call['raw_data']
    token = raw_data.get('token', {})
    trade = raw_data.get('trade', {})
    
    ticker = token.get('symbol', 'UNKNOWN')
    krom_price = trade.get('buyPrice', 0)
    buy_timestamp = trade.get('buyTimestamp', 0)
    contract = token.get('ca', '')
    network = token.get('network', 'solana')
    pool_address = token.get('pa', '')
    
    # Call edge function
    edge_price = test_edge_function(contract, network, buy_timestamp, pool_address)
    
    # Direct API call with ORIGINAL timestamp
    direct_data = get_direct_ohlcv(network, pool_address, buy_timestamp)
    
    # Direct API call with ADJUSTED timestamp (UTC-7)
    adjusted_timestamp = buy_timestamp - 25200
    direct_data_adjusted = get_direct_ohlcv(network, pool_address, adjusted_timestamp)
    
    # Format results
    if direct_data and 'close' in direct_data:
        direct_price = direct_data['close']
        direct_str = f"${direct_price:.8f}"
        direct_diff = ((direct_price - krom_price) / krom_price) * 100
        direct_diff_str = f"{direct_diff:+.1f}%"
    else:
        direct_str = "None"
        direct_diff_str = "N/A"
    
    if edge_price:
        edge_str = f"${edge_price:.8f}"
        edge_diff = ((edge_price - krom_price) / krom_price) * 100
        edge_diff_str = f"{edge_diff:+.1f}%"
    else:
        edge_str = "None"
        edge_diff_str = "N/A"
    
    krom_str = f"${krom_price:.8f}"
    
    print(f"{ticker:<10} {krom_str:<15} {edge_str:<15} {direct_str:<15} {edge_diff_str:<15} {direct_diff_str}")
    
    # Show details if there's a big discrepancy
    if edge_price and direct_data and 'close' in direct_data:
        if abs(edge_price - direct_data['close']) > 0.00000001:
            print(f"  ⚠️  Edge and Direct API prices differ!")
            if direct_data_adjusted and 'close' in direct_data_adjusted:
                print(f"  Direct w/ adjusted time: ${direct_data_adjusted['close']:.8f}")
            else:
                print(f"  Direct w/ adjusted time: No data")
            print(f"  Original time: {datetime.fromtimestamp(buy_timestamp)}")
            print(f"  Adjusted time: {datetime.fromtimestamp(adjusted_timestamp)}")
    
    time.sleep(1)  # Rate limit

print("\n" + "="*90)
print("\nDETAILED TEST WITH DOGSHIT:")

# Get DOGSHIT for detailed test
url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
url += "?select=*&ticker=eq.DOGSHIT&raw_data->trade->buyPrice=not.is.null&limit=1"

req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)

response = urllib.request.urlopen(req)
calls = json.loads(response.read().decode())

if calls:
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
    
    print(f"\nToken: {ticker}")
    print(f"KROM price: ${krom_price:.8f}")
    print(f"Timestamp: {buy_timestamp} = {datetime.fromtimestamp(buy_timestamp)}")
    print(f"Pool: {pool_address}")
    
    # Test with original timestamp
    print(f"\n1. Direct API with ORIGINAL timestamp:")
    direct_orig = get_direct_ohlcv(network, pool_address, buy_timestamp)
    if direct_orig and 'close' in direct_orig:
        print(f"   Close price: ${direct_orig['close']:.8f}")
        print(f"   Candle time: {datetime.fromtimestamp(direct_orig['timestamp'])}")
        diff = ((direct_orig['close'] - krom_price) / krom_price) * 100
        print(f"   Diff from KROM: {diff:+.2f}%")
    else:
        print(f"   Error: {direct_orig}")
    
    # Test with adjusted timestamp
    print(f"\n2. Direct API with ADJUSTED timestamp (UTC-7):")
    adjusted_ts = buy_timestamp - 25200
    direct_adj = get_direct_ohlcv(network, pool_address, adjusted_ts)
    if direct_adj and 'close' in direct_adj:
        print(f"   Close price: ${direct_adj['close']:.8f}")
        print(f"   Candle time: {datetime.fromtimestamp(direct_adj['timestamp'])}")
        diff = ((direct_adj['close'] - krom_price) / krom_price) * 100
        print(f"   Diff from KROM: {diff:+.2f}%")
    else:
        print(f"   Error: {direct_adj}")
    
    # Test edge function
    print(f"\n3. Edge function result:")
    edge_price = test_edge_function(contract, network, buy_timestamp, pool_address)
    if edge_price:
        print(f"   Price: ${edge_price:.8f}")
        diff = ((edge_price - krom_price) / krom_price) * 100
        print(f"   Diff from KROM: {diff:+.2f}%")
    else:
        print(f"   No price returned")