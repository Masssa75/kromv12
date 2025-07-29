import json
import urllib.request
import time
from datetime import datetime

# Direct comparison of OHLCV data from different pools

# SLOP data
contract = "2uaTpSujZBYwBZNXusmW7PqM8Vi4qwbyotnfWhaN9oT9"
network = "solana"
timestamp = 1753662600  # 2025-07-28 08:30:00
krom_pool = "DwTSZ1Jk2H1d8Dshgyg1xBfyNhoTmbwczjM4w2FfHdA2"
krom_price = 0.00241937

print("=== Direct OHLCV Comparison ===")
print(f"Token: SLOP")
print(f"KROM price: ${krom_price:.8f}")
print(f"Timestamp: {timestamp} ({datetime.fromtimestamp(timestamp)})")
print()

# Function to get OHLCV data
def get_ohlcv(network, pool_address, timestamp, name="Pool"):
    print(f"\n{name}: {pool_address[:20]}...")
    
    # Try minute data
    before_timestamp = timestamp + 300
    url = f"https://api.geckoterminal.com/api/v2/networks/{network}/pools/{pool_address}/ohlcv/minute"
    url += f"?before_timestamp={before_timestamp}&limit=10&currency=usd"
    
    try:
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0')  # Add user agent
        
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        
        ohlcv_list = data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
        
        if not ohlcv_list:
            print("  No OHLCV data available")
            return None
            
        # Find closest candle
        closest = None
        for candle in ohlcv_list:
            candle_time = candle[0]
            if abs(candle_time - timestamp) <= 60:
                closest = candle
                break
        
        if closest:
            candle_time, open_p, high, low, close, volume = closest
            time_diff = candle_time - timestamp
            
            print(f"  Found candle at {datetime.fromtimestamp(candle_time)} ({time_diff:+d} seconds)")
            print(f"  Open:  ${open_p:.8f}")
            print(f"  High:  ${high:.8f}")
            print(f"  Low:   ${low:.8f}")
            print(f"  Close: ${close:.8f} ← Edge function returns this")
            print(f"  Volume: ${volume:.2f}")
            
            # Check if KROM price is in range
            in_range = low <= krom_price <= high
            print(f"  KROM price in OHLC range: {'✅ YES' if in_range else '❌ NO'}")
            
            if not in_range:
                print(f"  Price difference: {((close - krom_price) / krom_price * 100):+.2f}%")
            
            return close
        else:
            print(f"  No candle within 60 seconds of timestamp")
            return None
            
    except Exception as e:
        print(f"  Error: {e}")
        return None

# Test 1: KROM's pool
krom_close = get_ohlcv(network, krom_pool, timestamp, "KROM's Pool")
time.sleep(1)  # Rate limit

# Test 2: Try to find other pools
print("\n" + "="*50)
print("\nSearching for other pools...")

# Get pools for this token
try:
    url = f"https://api.geckoterminal.com/api/v2/networks/{network}/tokens/{contract}/pools"
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0')
    
    response = urllib.request.urlopen(req)
    data = json.loads(response.read().decode())
    
    pools = data.get('data', [])
    print(f"Found {len(pools)} pools for SLOP")
    
    # Check top 3 pools
    for i, pool in enumerate(pools[:3]):
        if i > 0:
            time.sleep(1)  # Rate limit
            
        attrs = pool['attributes']
        pool_addr = attrs['address']
        liquidity = float(attrs.get('reserve_in_usd', '0'))
        
        print(f"\n#{i+1} Pool liquidity: ${liquidity:,.2f}")
        
        if pool_addr == krom_pool:
            print("   ✅ This is KROM's pool")
        else:
            # Get OHLCV for this pool
            other_close = get_ohlcv(network, pool_addr, timestamp, f"Pool #{i+1}")
            if other_close and other_close != krom_close:
                print(f"\n   🔄 DIFFERENT PRICE from KROM's pool!")
                print(f"   This pool: ${other_close:.8f}")
                print(f"   KROM pool: ${krom_close:.8f}" if krom_close else "   KROM pool: No data")
                
except Exception as e:
    print(f"Error getting pools: {e}")

print("\n" + "="*50)
print("\nCONCLUSION:")
print("If different pools show different prices, the edge function")
print("should return different results when given different pool addresses.")