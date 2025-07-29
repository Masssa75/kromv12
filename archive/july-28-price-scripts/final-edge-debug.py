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

print("=== Final Edge Function Debug ===")
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
print(f"KROM price: ${krom_price:.8f}")
print(f"KROM timestamp: {buy_timestamp} = {datetime.fromtimestamp(buy_timestamp)}")
print()

# Direct API to find available candles
print("1. Finding available candles around KROM timestamp:")
base_url = "https://api.geckoterminal.com/api/v2"

# Get candles BEFORE the timestamp
before_ts = buy_timestamp - 300  # 5 minutes before
url = f"{base_url}/networks/{network}/pools/{pool_address}/ohlcv/minute"
url += f"?before_timestamp={buy_timestamp}&limit=10&currency=usd"

req = urllib.request.Request(url)
req.add_header('User-Agent', 'Mozilla/5.0')

try:
    response = urllib.request.urlopen(req)
    data = json.loads(response.read().decode())
    ohlcv_list = data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
    
    print(f"   Found {len(ohlcv_list)} candles AFTER timestamp {buy_timestamp}:")
    closest_candle = None
    closest_diff = float('inf')
    
    for candle in ohlcv_list:
        candle_time = candle[0]
        diff = abs(candle_time - buy_timestamp)
        if diff < closest_diff:
            closest_diff = diff
            closest_candle = candle
        
        if diff <= 300:  # Show candles within 5 minutes
            print(f"   - {datetime.fromtimestamp(candle_time)} (diff: {candle_time - buy_timestamp:+d}s) - Close: ${candle[4]:.8f}")
    
    if closest_candle:
        print(f"\n   Closest candle:")
        print(f"   Time: {datetime.fromtimestamp(closest_candle[0])} (diff: {closest_diff}s)")
        print(f"   OHLC: ${closest_candle[1]:.8f} / ${closest_candle[2]:.8f} / ${closest_candle[3]:.8f} / ${closest_candle[4]:.8f}")
        
        # Price comparison
        close_price = closest_candle[4]
        diff_pct = ((close_price - krom_price) / krom_price) * 100
        print(f"   Close vs KROM: {diff_pct:+.2f}%")
        
except Exception as e:
    print(f"   Error: {e}")

# Try getting candles with AFTER timestamp to see range
print(f"\n2. Getting candles BEFORE timestamp:")
after_ts = buy_timestamp + 600  # 10 minutes after
url = f"{base_url}/networks/{network}/pools/{pool_address}/ohlcv/minute"
url += f"?after_timestamp={buy_timestamp}&limit=5&currency=usd"

req = urllib.request.Request(url)
req.add_header('User-Agent', 'Mozilla/5.0')

try:
    response = urllib.request.urlopen(req)
    data = json.loads(response.read().decode())
    ohlcv_list = data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
    
    if ohlcv_list:
        print(f"   Found {len(ohlcv_list)} candles BEFORE timestamp:")
        for candle in ohlcv_list[:3]:
            candle_time = candle[0]
            print(f"   - {datetime.fromtimestamp(candle_time)} (diff: {candle_time - buy_timestamp:+d}s) - Close: ${candle[4]:.8f}")
            
except Exception as e:
    print(f"   Error: {e}")

print("\n" + "="*60)
print("\nCONCLUSION:")
print("The edge function might be:")
print("1. Not finding candles within 60 seconds of the timestamp")
print("2. Using a different timeframe (hour/day) when minute data isn't available")
print("3. Having issues with the pool address parameter")
print("\nThe direct API shows the closest available candle and its price difference.")