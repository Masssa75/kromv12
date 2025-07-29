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

print("=== Testing Timestamp Formats ===")
print()

# Get DOGSHIT data
url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
url += "?select=*&ticker=eq.DOGSHIT&raw_data->trade->buyPrice=not.is.null&limit=1"

req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)

response = urllib.request.urlopen(req)
calls = json.loads(response.read().decode())
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

print(f"Token: {ticker}")
print(f"KROM timestamp from DB: {buy_timestamp}")
print(f"Type: {type(buy_timestamp)}")
print(f"Length: {len(str(buy_timestamp))}")
print(f"Is it seconds? {datetime.fromtimestamp(buy_timestamp)}")
print(f"Is it milliseconds? {datetime.fromtimestamp(buy_timestamp/1000)}")
print()

# Check what format GeckoTerminal expects
print("Testing GeckoTerminal API with different timestamp formats:")
base_url = "https://api.geckoterminal.com/api/v2"

# Test 1: Timestamp as is (10 digits - seconds)
print(f"\n1. Using timestamp as-is ({buy_timestamp}):")
url = f"{base_url}/networks/{network}/pools/{pool_address}/ohlcv/minute"
url += f"?before_timestamp={buy_timestamp}&limit=3&currency=usd"

req = urllib.request.Request(url)
req.add_header('User-Agent', 'Mozilla/5.0')

try:
    response = urllib.request.urlopen(req)
    data = json.loads(response.read().decode())
    ohlcv_list = data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
    
    if ohlcv_list:
        print(f"   ✅ Success! Found {len(ohlcv_list)} candles")
        first_candle = ohlcv_list[0]
        print(f"   First candle time: {first_candle[0]} = {datetime.fromtimestamp(first_candle[0])}")
        print(f"   Close price: ${first_candle[4]:.8f}")
    else:
        print(f"   ❌ No data returned")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Convert to milliseconds (13 digits)
print(f"\n2. Converting to milliseconds ({buy_timestamp * 1000}):")
url = f"{base_url}/networks/{network}/pools/{pool_address}/ohlcv/minute"
url += f"?before_timestamp={buy_timestamp * 1000}&limit=3&currency=usd"

req = urllib.request.Request(url)
req.add_header('User-Agent', 'Mozilla/5.0')

try:
    response = urllib.request.urlopen(req)
    data = json.loads(response.read().decode())
    ohlcv_list = data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
    
    if ohlcv_list:
        print(f"   ✅ Success! Found {len(ohlcv_list)} candles")
        first_candle = ohlcv_list[0]
        candle_ts = first_candle[0]
        # Check if returned timestamp is in ms or seconds
        if candle_ts > 1000000000000:
            print(f"   First candle time: {candle_ts} = {datetime.fromtimestamp(candle_ts/1000)} (milliseconds)")
        else:
            print(f"   First candle time: {candle_ts} = {datetime.fromtimestamp(candle_ts)} (seconds)")
        print(f"   Close price: ${first_candle[4]:.8f}")
    else:
        print(f"   ❌ No data returned")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Check edge function behavior
print(f"\n3. Edge function call:")
edge_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-single"

payload = {
    "contractAddress": contract,
    "network": network,
    "callTimestamp": buy_timestamp,  # Sending as seconds
    "poolAddress": pool_address
}

data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(edge_url, data=data)
req.add_header('Content-Type', 'application/json')
req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')

try:
    response = urllib.request.urlopen(req)
    result = json.loads(response.read().decode())
    
    print(f"   Price returned: {result.get('priceAtCall')}")
    print(f"   Call date: {result.get('callDate')}")
    
    # Check if edge function is converting properly
    edge_ts = result.get('callDate')
    if edge_ts:
        # Parse ISO date
        edge_datetime = datetime.fromisoformat(edge_ts.replace('Z', '+00:00'))
        edge_unix = int(edge_datetime.timestamp())
        print(f"   Edge function used timestamp: {edge_unix}")
        print(f"   Difference from original: {edge_unix - buy_timestamp} seconds")
        
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "="*60)
print("\nCONCLUSION:")
print("Check which timestamp format works with GeckoTerminal API")
print("and whether the edge function is converting timestamps correctly.")