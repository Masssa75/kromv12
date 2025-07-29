import json
import urllib.request
import time
from datetime import datetime

def test_with_resolution(network, pool_address, timestamp, token_name):
    """Test GeckoTerminal API with resolution parameter"""
    base_url = "https://api.geckoterminal.com/api/v2"
    
    print(f"\n=== Testing Resolution Parameter: {token_name} ===")
    print(f"Network: {network}")
    print(f"Pool: {pool_address}")
    print(f"Timestamp: {timestamp} = {datetime.fromtimestamp(timestamp)}")
    
    # Test different resolution values
    resolutions = ['1m', '5m', '15m', '1h', '4h', '1d']
    
    for resolution in resolutions:
        print(f"\n--- Testing resolution: {resolution} ---")
        
        # Try the resolution parameter in OHLCV endpoint
        ohlcv_url = f"{base_url}/networks/{network}/pools/{pool_address}/ohlcv"
        ohlcv_url += f"?resolution={resolution}&before_timestamp={timestamp + 300}&limit=5&currency=usd"
        print(f"URL: {ohlcv_url}")
        
        req = urllib.request.Request(ohlcv_url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        
        try:
            response = urllib.request.urlopen(req)
            data = json.loads(response.read().decode())
            ohlcv_list = data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
            
            if ohlcv_list:
                print(f"   ✅ Found {len(ohlcv_list)} candles with resolution {resolution}")
                
                # Find closest candle to our timestamp
                closest_diff = float('inf')
                closest_candle = None
                
                for candle in ohlcv_list:
                    diff = abs(candle[0] - timestamp)
                    if diff < closest_diff:
                        closest_diff = diff
                        closest_candle = candle
                
                if closest_candle:
                    print(f"   Closest candle: {closest_diff} seconds away")
                    print(f"   Time: {datetime.fromtimestamp(closest_candle[0])}")
                    print(f"   Close price: ${closest_candle[4]:.8f}")
                    
                    if closest_diff <= 3600:  # Within 1 hour
                        print(f"   🎯 GOOD DATA with resolution {resolution}!")
                        return closest_candle[4], resolution
            else:
                print(f"   ❌ No data with resolution {resolution}")
                
        except urllib.error.HTTPError as e:
            print(f"   ❌ HTTP Error with resolution {resolution}: {e.code} - {e.reason}")
        except Exception as e:
            print(f"   ❌ Error with resolution {resolution}: {e}")
        
        time.sleep(0.3)  # Rate limiting
    
    return None, None

print("=== Testing Resolution Parameter on Failed Tokens ===")
print(f"Date: {datetime.now()}")

# Test a few failed tokens with resolution parameter
failed_cases = [
    {
        "token": "PEPE",
        "network": "ethereum", 
        "pool": "0x67F3Bc3B3EcBd68c79dffD22666a04e6d3f35b15",
        "timestamp": 1747598880,
        "krom_price": 0.00119866
    },
    {
        "token": "YIPPITY",
        "network": "ethereum",
        "pool": "0xdB97400565698b3Ae7c901EE72C8920d0cd0DAD2", 
        "timestamp": 1747703880,
        "krom_price": 0.00000010
    },
    {
        "token": "MOANER",
        "network": "ethereum",
        "pool": "0x1793C59e9e8793e807c0de7330C2293bD2a76865",
        "timestamp": 1747788480, 
        "krom_price": 0.00020231
    }
]

print(f"Testing resolution parameter on {len(failed_cases)} tokens that previously failed...")

results = []

for case in failed_cases:
    price, resolution = test_with_resolution(
        case["network"],
        case["pool"], 
        case["timestamp"],
        case["token"]
    )
    
    if price:
        krom_price = case["krom_price"]
        diff = ((price - krom_price) / krom_price) * 100 if krom_price > 0 else 0
        
        results.append({
            "token": case["token"],
            "resolution": resolution,
            "api_price": price,
            "krom_price": krom_price,
            "difference": diff
        })
        
        print(f"\n   💰 SUCCESS WITH RESOLUTION!")
        print(f"   Resolution: {resolution}")
        print(f"   KROM price: ${krom_price:.8f}")
        print(f"   API price:  ${price:.8f}")
        print(f"   Difference: {diff:+.2f}%")
    else:
        print(f"\n   ❌ No data found with any resolution")
    
    print(f"\n{'='*80}")
    time.sleep(2)  # Rate limiting between tokens

# Summary
print(f"\nSUMMARY:")
print(f"Tokens tested with resolution parameter: {len(failed_cases)}")
print(f"Successful with resolution: {len(results)}")

if results:
    print(f"\nSUCCESSES:")
    for r in results:
        print(f"  {r['token']}: Resolution {r['resolution']} - ${r['api_price']:.8f} ({r['difference']:+.2f}% vs KROM)")
    
    print(f"\n🎉 Resolution parameter found data for previously failed tokens!")
    print(f"Your developer was right - resolution parameter is the key!")
else:
    print(f"\nNo successes with resolution parameter either.")