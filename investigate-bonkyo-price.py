import json
import urllib.request
from datetime import datetime

# BONKYO details from test
contract = "oha3mwwm2tqWRouJ2KGUiz4Vz9FCRcPm1fApm87bonk"
pool = "8Vnm5KtT1bkU9ASs4XhMd7N1B7xbUhGZLM6DmnqGmF7T"
krom_price = 0.0002194881795206477
timestamp = 1751520127  # From raw_data

print("=== Investigating BONKYO Price Mismatch ===")
print(f"Contract: {contract}")
print(f"Pool: {pool}")
print(f"KROM Price: ${krom_price}")
print(f"Timestamp: {datetime.fromtimestamp(timestamp).isoformat()}")

# Direct GeckoTerminal API call with minute candles
url = f"https://api.geckoterminal.com/api/v2/networks/solana/pools/{pool}/ohlcv/minute"
url += f"?before_timestamp={timestamp + 300}&limit=10&currency=usd"

print(f"\nFetching minute candles around {timestamp}...")
print(f"URL: {url}")

try:
    response = urllib.request.urlopen(url)
    data = json.loads(response.read().decode())
    
    ohlcv_list = data['data']['attributes']['ohlcv_list']
    
    print(f"\nFound {len(ohlcv_list)} minute candles:")
    print("Timestamp, Open, High, Low, Close, Volume")
    
    for candle in ohlcv_list:
        candle_time = datetime.fromtimestamp(candle[0])
        time_diff = candle[0] - timestamp
        print(f"{candle_time.isoformat()} ({time_diff:+d}s): ${candle[1]:.8f}, ${candle[2]:.8f}, ${candle[3]:.8f}, ${candle[4]:.8f}, Vol: ${candle[5]:.2f}")
        
        # Check if KROM price falls within this candle
        if candle[3] <= krom_price <= candle[2]:  # between low and high
            print(f"  ✅ KROM price ${krom_price} is within this candle range!")
    
    # Find the closest candle
    closest_candle = min(ohlcv_list, key=lambda x: abs(x[0] - timestamp))
    closest_time = datetime.fromtimestamp(closest_candle[0])
    time_diff = closest_candle[0] - timestamp
    
    print(f"\nClosest candle: {closest_time.isoformat()} ({time_diff:+d}s away)")
    print(f"Price range: ${closest_candle[3]:.8f} - ${closest_candle[2]:.8f}")
    print(f"KROM price: ${krom_price:.8f}")
    
    if closest_candle[3] <= krom_price <= closest_candle[2]:
        print("✅ KROM price is within the candle range!")
    else:
        print("❌ KROM price is outside the candle range")
        
except Exception as e:
    print(f"Error: {e}")

# Let's also check if this might be a different pool issue
print("\n=== Checking for other pools ===")
pools_url = f"https://api.geckoterminal.com/api/v2/networks/solana/tokens/{contract}/pools"

try:
    response = urllib.request.urlopen(pools_url)
    data = json.loads(response.read().decode())
    
    pools = data.get('data', [])
    print(f"Found {len(pools)} pools for this token:")
    
    for p in pools[:5]:  # Show top 5
        attrs = p['attributes']
        print(f"\nPool: {attrs['address']}")
        print(f"  Pair: {attrs['name']}")
        print(f"  Price: ${attrs.get('token_price_usd', 'N/A')}")
        print(f"  Liquidity: ${attrs.get('reserve_in_usd', 'N/A')}")
        
        if attrs['address'] == pool:
            print("  👆 This is KROM's pool")
            
except Exception as e:
    print(f"Error fetching pools: {e}")