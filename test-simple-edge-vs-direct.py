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

SUPABASE_SERVICE_ROLE_KEY = env_vars['SUPABASE_SERVICE_ROLE_KEY']

# Simple test with known data
contract = "8AKBy6SkaerTMWZAad47AYk4yKWo2Kx6R3VWzJ3zpump"  # DOGSHIT
network = "solana"
timestamp = 1753670460  # 2025-07-28 09:41:00
pool_address = "8MwvGfxqAuMAT1VxLFPruwzUku71divymByUFRxjQUyV"
krom_price = 0.00209194

print("=== Simple Edge vs Direct Comparison ===")
print(f"Token: DOGSHIT")
print(f"KROM price: ${krom_price:.8f}")
print(f"Timestamp: {timestamp} ({datetime.fromtimestamp(timestamp)})")
print(f"Pool: {pool_address}")
print()

# 1. Direct API call
print("1. Direct GeckoTerminal API:")
base_url = "https://api.geckoterminal.com/api/v2"
before_timestamp = timestamp + 300  # 5 minutes after

# Try minute candles
url = f"{base_url}/networks/{network}/pools/{pool_address}/ohlcv/minute"
url += f"?before_timestamp={before_timestamp}&limit=5&currency=usd"

print(f"   URL: {url}")

req = urllib.request.Request(url)
req.add_header('User-Agent', 'Mozilla/5.0')

try:
    response = urllib.request.urlopen(req)
    data = json.loads(response.read().decode())
    ohlcv_list = data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
    
    if ohlcv_list:
        print(f"   Found {len(ohlcv_list)} candles:")
        for i, candle in enumerate(ohlcv_list[:3]):
            candle_time, open_p, high, low, close, volume = candle
            time_diff = candle_time - timestamp
            print(f"   Candle {i+1}: {datetime.fromtimestamp(candle_time)} ({time_diff:+d}s)")
            print(f"      OHLC: ${open_p:.8f} / ${high:.8f} / ${low:.8f} / ${close:.8f}")
            
            # Check if this is the candle edge function should use
            if abs(time_diff) <= 60:
                print(f"      ✅ This is within 60 seconds - Edge should use CLOSE: ${close:.8f}")
                expected_edge_price = close
except Exception as e:
    print(f"   Error: {e}")
    expected_edge_price = None

# 2. Edge function call
print(f"\n2. Edge Function Call:")
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
    
    edge_price = result.get('priceAtCall')
    if edge_price:
        print(f"   Edge price: ${edge_price:.8f}")
        diff = ((edge_price - krom_price) / krom_price) * 100
        print(f"   Diff from KROM: {diff:+.2f}%")
        
        if expected_edge_price:
            if abs(edge_price - expected_edge_price) < 0.00000001:
                print(f"   ✅ Matches expected close price!")
            else:
                print(f"   ❌ Does NOT match expected close price ${expected_edge_price:.8f}")
                edge_diff = ((edge_price - expected_edge_price) / expected_edge_price) * 100
                print(f"   Edge vs Expected: {edge_diff:+.2f}%")
    else:
        print(f"   No price returned")
        print(f"   Full response: {json.dumps(result, indent=2)}")
        
except Exception as e:
    print(f"   Error: {e}")

# 3. Try hour candles to see if edge function is using wrong timeframe
print(f"\n3. Checking Hour Candles (in case edge function uses these):")
url = f"{base_url}/networks/{network}/pools/{pool_address}/ohlcv/hour"
url += f"?before_timestamp={before_timestamp}&limit=3&currency=usd"

req = urllib.request.Request(url)
req.add_header('User-Agent', 'Mozilla/5.0')

try:
    response = urllib.request.urlopen(req)
    data = json.loads(response.read().decode())
    ohlcv_list = data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
    
    if ohlcv_list:
        for i, candle in enumerate(ohlcv_list[:2]):
            candle_time, open_p, high, low, close, volume = candle
            print(f"   Hour candle: {datetime.fromtimestamp(candle_time)}")
            print(f"      Close: ${close:.8f}")
            
            # Check if edge price matches any hour candle
            if edge_price and abs(edge_price - close) < 0.00000001:
                print(f"      ⚠️  Edge price matches this HOUR candle close!")
                
except Exception as e:
    print(f"   Error: {e}")