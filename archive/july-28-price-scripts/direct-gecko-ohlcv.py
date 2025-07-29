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

def get_sample_calls():
    """Get a few calls to test"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += "?select=krom_id,ticker,raw_data"
    url += "&raw_data->trade->buyPrice=not.is.null"
    url += "&ticker=in.(KITTEN,DOGSHIT,SLOP)"  # Specific tokens that showed data
    url += "&limit=3"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error: {e}")
        return []

def fetch_ohlcv_direct(network, pool_address, before_timestamp):
    """Direct call to GeckoTerminal OHLCV API"""
    # GeckoTerminal expects timestamps in seconds
    # OHLCV endpoint format based on common API patterns
    url = f"https://api.geckoterminal.com/api/v2/networks/{network}/pools/{pool_address}/ohlcv/minute"
    url += f"?aggregate=1"  # 1 minute candles
    url += f"&before_timestamp={before_timestamp}"
    url += f"&limit=10"  # Get 10 candles before the timestamp
    
    req = urllib.request.Request(url)
    # Add headers that might help avoid 403
    req.add_header('Accept', 'application/json')
    req.add_header('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        return data
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}", "body": e.read().decode()[:200]}
    except Exception as e:
        return {"error": str(e)}

def find_exact_candle(ohlcv_list, target_timestamp):
    """Find the candle that contains our timestamp"""
    # OHLCV format is typically: [timestamp, open, high, low, close, volume]
    for candle in ohlcv_list:
        candle_time = candle[0]
        # Check if our timestamp falls within this minute
        if candle_time <= target_timestamp < candle_time + 60:
            return {
                "timestamp": candle_time,
                "open": candle[1],
                "high": candle[2],
                "low": candle[3],
                "close": candle[4],
                "volume": candle[5],
                "time": datetime.fromtimestamp(candle_time).strftime('%H:%M:%S')
            }
    return None

print("=== Direct GeckoTerminal OHLCV Analysis ===")
print(f"Time: {datetime.now()}\n")

# Get sample calls
calls = get_sample_calls()
print(f"Testing {len(calls)} calls...\n")

for call in calls:
    ticker = call.get('ticker')
    raw_data = call.get('raw_data', {})
    trade = raw_data.get('trade', {})
    token = raw_data.get('token', {})
    
    krom_price = trade.get('buyPrice')
    buy_timestamp = trade.get('buyTimestamp')
    pool_address = token.get('pa')  # Pool address
    network = token.get('network', 'solana')
    
    if not all([krom_price, buy_timestamp, pool_address]):
        continue
    
    buy_time = datetime.fromtimestamp(buy_timestamp)
    
    print(f"=== {ticker} ===")
    print(f"Buy time: {buy_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"KROM price: ${krom_price:.8f}")
    print(f"Pool: {pool_address[:20]}...")
    
    # Try direct OHLCV fetch
    print("\nFetching OHLCV data...")
    ohlcv_data = fetch_ohlcv_direct(network, pool_address, buy_timestamp + 60)
    
    if "error" in ohlcv_data:
        print(f"Error: {ohlcv_data['error']}")
        if "body" in ohlcv_data:
            print(f"Response: {ohlcv_data['body']}")
    else:
        # Parse OHLCV response
        ohlcv_list = ohlcv_data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
        
        if ohlcv_list:
            print(f"Got {len(ohlcv_list)} candles")
            
            # Find the exact minute candle
            exact_candle = find_exact_candle(ohlcv_list, buy_timestamp)
            
            if exact_candle:
                print(f"\nMinute candle at {exact_candle['time']}:")
                print(f"  Open:  ${exact_candle['open']:.8f}")
                print(f"  High:  ${exact_candle['high']:.8f}")
                print(f"  Low:   ${exact_candle['low']:.8f}")
                print(f"  Close: ${exact_candle['close']:.8f}")
                
                # Compare with KROM price
                print(f"\nKROM price: ${krom_price:.8f}")
                
                # Check if KROM price is within the candle range
                if exact_candle['low'] <= krom_price <= exact_candle['high']:
                    print("✅ KROM price is within the candle range!")
                    
                    # Calculate position within candle
                    open_diff = abs(krom_price - exact_candle['open']) / exact_candle['open'] * 100
                    close_diff = abs(krom_price - exact_candle['close']) / exact_candle['close'] * 100
                    
                    print(f"  Diff from open: {open_diff:.1f}%")
                    print(f"  Diff from close: {close_diff:.1f}%")
                else:
                    print("❌ KROM price is OUTSIDE the candle range!")
                    
                    if krom_price < exact_candle['low']:
                        diff = (exact_candle['low'] - krom_price) / krom_price * 100
                        print(f"  KROM is {diff:.1f}% BELOW the low")
                    else:
                        diff = (krom_price - exact_candle['high']) / exact_candle['high'] * 100
                        print(f"  KROM is {diff:.1f}% ABOVE the high")
            else:
                print("Could not find exact minute candle")
                # Show nearby candles
                print("\nNearby candles:")
                for candle in ohlcv_list[:3]:
                    candle_time = datetime.fromtimestamp(candle[0])
                    print(f"  {candle_time.strftime('%H:%M:%S')}: O=${candle[1]:.8f} C=${candle[4]:.8f}")
        else:
            print("No OHLCV data in response")
    
    print("\n" + "-"*50 + "\n")
    time.sleep(2)  # Rate limit

print("=== Summary ===")
print("KROM prices should fall within the minute candle's low-high range")
print("If they don't, it indicates:")
print("1. Wrong pool being queried")
print("2. Timestamp mismatch")
print("3. Different price source")
print("4. Data quality issues")