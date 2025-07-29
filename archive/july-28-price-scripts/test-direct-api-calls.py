import json
import urllib.request
import time
from datetime import datetime

def test_direct_api_call(network, pool_address, token_name, timestamp):
    """Test direct GeckoTerminal API calls"""
    base_url = "https://api.geckoterminal.com/api/v2"
    
    print(f"\n=== DIRECT API TEST: {token_name} ===")
    print(f"Network: {network}")
    print(f"Pool: {pool_address}")
    print(f"Timestamp: {timestamp} = {datetime.fromtimestamp(timestamp)}")
    
    # Test 1: Pool info endpoint
    print(f"\n1. Testing pool info endpoint:")
    pool_url = f"{base_url}/networks/{network}/pools/{pool_address}"
    print(f"   URL: {pool_url}")
    
    req = urllib.request.Request(pool_url)
    req.add_header('User-Agent', 'Mozilla/5.0')
    
    try:
        response = urllib.request.urlopen(req)
        print(f"   Status: {response.getcode()}")
        
        data = json.loads(response.read().decode())
        if data.get('data'):
            attrs = data['data']['attributes']
            print(f"   ✅ Pool exists!")
            print(f"   Name: {attrs.get('name', 'Unknown')}")
            print(f"   Base token: {attrs.get('base_token_price_usd', 'N/A')}")
            print(f"   Reserve: ${float(attrs.get('reserve_in_usd', 0)):,.2f}")
        else:
            print(f"   ❌ No pool data in response")
    except urllib.error.HTTPError as e:
        print(f"   ❌ HTTP Error: {e.code} - {e.reason}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: OHLCV endpoint
    print(f"\n2. Testing OHLCV endpoint:")
    before_timestamp = timestamp + 300  # 5 minutes after
    ohlcv_url = f"{base_url}/networks/{network}/pools/{pool_address}/ohlcv/minute"
    ohlcv_url += f"?before_timestamp={before_timestamp}&limit=5&currency=usd"
    print(f"   URL: {ohlcv_url}")
    
    req = urllib.request.Request(ohlcv_url)
    req.add_header('User-Agent', 'Mozilla/5.0')
    
    try:
        response = urllib.request.urlopen(req)
        print(f"   Status: {response.getcode()}")
        
        data = json.loads(response.read().decode())
        ohlcv_list = data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
        
        if ohlcv_list:
            print(f"   ✅ Found {len(ohlcv_list)} candles")
            
            # Find closest candle
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
                print(f"   OHLC: {closest_candle[1]:.8f} / {closest_candle[2]:.8f} / {closest_candle[3]:.8f} / {closest_candle[4]:.8f}")
                
                if closest_diff <= 300:
                    print(f"   🎯 USABLE DATA FOUND!")
                    return closest_candle[4]  # return close price
        else:
            print(f"   ❌ No OHLCV data returned")
            
    except urllib.error.HTTPError as e:
        print(f"   ❌ HTTP Error: {e.code} - {e.reason}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    return None

print("=== DIRECT API TESTING FOR FAILED TOKENS ===")
print(f"Date: {datetime.now()}")

# Test the exact failed cases with real data from our database
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
    },
    {
        "token": "WHITEY",
        "network": "ethereum",
        "pool": "0x1065b57045b6A1bc652859985A7094f2AcFd9048",
        "timestamp": 1747886880,
        "krom_price": 0.00003093
    },
    {
        "token": "FINTAI", 
        "network": "ethereum",
        "pool": "0x4dE0F9891E42510367599B55D63114a125F684F0",
        "timestamp": 1748093220,
        "krom_price": 0.00095458
    }
]

results = []

for case in failed_cases:
    api_price = test_direct_api_call(
        case["network"],
        case["pool"], 
        case["token"],
        case["timestamp"]
    )
    
    if api_price:
        krom_price = case["krom_price"]
        diff = ((api_price - krom_price) / krom_price) * 100 if krom_price > 0 else 0
        
        results.append({
            "token": case["token"],
            "api_price": api_price,
            "krom_price": krom_price,
            "difference": diff
        })
        
        print(f"\n   💰 PRICE COMPARISON:")
        print(f"   KROM price: ${krom_price:.8f}")
        print(f"   API price:  ${api_price:.8f}")
        print(f"   Difference: {diff:+.2f}%")
    
    print(f"\n{'='*60}")
    time.sleep(1)  # Rate limiting

# Summary
print(f"\nSUMMARY OF DIRECT API TESTS:")
print(f"Total tokens tested: {len(failed_cases)}")
print(f"Successful API calls: {len(results)}")

if results:
    print(f"\nSUCCESSFUL TOKENS:")
    for r in results:
        print(f"  {r['token']}: ${r['api_price']:.8f} ({r['difference']:+.2f}% vs KROM)")
    
    print(f"\nThis proves that GeckoTerminal DOES have data for these tokens!")
    print(f"The issue must be in our edge function implementation.")
else:
    print(f"\nNo successful API calls - the tokens truly don't exist in GeckoTerminal")