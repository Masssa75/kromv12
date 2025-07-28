import json
import urllib.request
import time
from datetime import datetime

def test_different_resolution_approaches(network, pool_address, timestamp, token_name, contract_address):
    """Test different ways to use resolution parameter"""
    base_url = "https://api.geckoterminal.com/api/v2"
    
    print(f"\n=== Testing Different Resolution Approaches: {token_name} ===")
    print(f"Network: {network}")
    print(f"Pool: {pool_address}")
    print(f"Contract: {contract_address}")
    print(f"Timestamp: {timestamp} = {datetime.fromtimestamp(timestamp)}")
    
    approaches = [
        # Approach 1: Resolution in different endpoint formats
        {
            "name": "Standard OHLCV with resolution",
            "url": f"{base_url}/networks/{network}/pools/{pool_address}/ohlcv?resolution=1m&before_timestamp={timestamp + 300}&limit=5"
        },
        {
            "name": "Token-based OHLCV with resolution",
            "url": f"{base_url}/networks/{network}/tokens/{contract_address}/ohlcv?resolution=1m&before_timestamp={timestamp + 300}&limit=5"
        },
        # Approach 2: Different timeframes
        {
            "name": "Minute endpoint (no resolution)",
            "url": f"{base_url}/networks/{network}/pools/{pool_address}/ohlcv/minute?before_timestamp={timestamp + 300}&limit=5"
        },
        {
            "name": "Hour endpoint (no resolution)", 
            "url": f"{base_url}/networks/{network}/pools/{pool_address}/ohlcv/hour?before_timestamp={timestamp + 3600}&limit=5"
        },
        {
            "name": "Day endpoint (no resolution)",
            "url": f"{base_url}/networks/{network}/pools/{pool_address}/ohlcv/day?before_timestamp={timestamp + 86400}&limit=5"
        },
        # Approach 3: Try without before_timestamp
        {
            "name": "Resolution without timestamp filter",
            "url": f"{base_url}/networks/{network}/pools/{pool_address}/ohlcv?resolution=1d&limit=100"
        },
        # Approach 4: Try current price endpoint
        {
            "name": "Current pool info",
            "url": f"{base_url}/networks/{network}/pools/{pool_address}"
        }
    ]
    
    for approach in approaches:
        print(f"\n--- {approach['name']} ---")
        print(f"URL: {approach['url']}")
        
        req = urllib.request.Request(approach['url'])
        req.add_header('User-Agent', 'Mozilla/5.0')
        
        try:
            response = urllib.request.urlopen(req)
            data = json.loads(response.read().decode())
            
            # Handle different response formats
            if 'ohlcv' in approach['name'].lower() or 'resolution' in approach['name'].lower():
                ohlcv_list = data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
                if ohlcv_list:
                    print(f"   ✅ Found {len(ohlcv_list)} candles!")
                    
                    # Show first few candles
                    for i, candle in enumerate(ohlcv_list[:3]):
                        candle_time = datetime.fromtimestamp(candle[0])
                        print(f"   Candle {i+1}: {candle_time} - Close: ${candle[4]:.8f}")
                    
                    return True, approach['name']
                else:
                    print(f"   ❌ No OHLCV data")
            else:
                # Pool info endpoint
                if data.get('data'):
                    attrs = data['data']['attributes']
                    print(f"   ✅ Pool exists!")
                    print(f"   Name: {attrs.get('name', 'Unknown')}")
                    print(f"   Base token price: ${attrs.get('base_token_price_usd', 'N/A')}")
                    print(f"   Reserve: ${float(attrs.get('reserve_in_usd', 0)):,.2f}")
                    return True, approach['name']
                else:
                    print(f"   ❌ No pool data")
                    
        except urllib.error.HTTPError as e:
            print(f"   ❌ HTTP Error: {e.code} - {e.reason}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        time.sleep(0.5)  # Rate limiting
    
    return False, None

print("=== Testing Alternative Resolution Methods ===")
print(f"Date: {datetime.now()}")

# Test one failed token with all different approaches
test_case = {
    "token": "PEPE",
    "network": "ethereum", 
    "pool": "0x67F3Bc3B3EcBd68c79dffD22666a04e6d3f35b15",
    "contract": "0x6e0abF27e4c3Adbe2661d45970f6e57525b72da3",
    "timestamp": 1747598880,
    "krom_price": 0.00119866
}

print(f"Testing all resolution approaches on {test_case['token']}...")

success, method = test_different_resolution_approaches(
    test_case["network"],
    test_case["pool"], 
    test_case["timestamp"],
    test_case["token"],
    test_case["contract"]
)

if success:
    print(f"\n🎉 SUCCESS! Method '{method}' found data for {test_case['token']}")
    print(f"Your developer was right about using a different approach!")
else:
    print(f"\n❌ No approach worked for {test_case['token']}")
    print(f"The token truly doesn't exist in GeckoTerminal")

print(f"\n{'='*80}")
print(f"\nNEXT STEPS:")
print(f"If any method worked above, we should:")
print(f"1. Update our edge function to use the successful method")
print(f"2. Test it on all 12 failed tokens")
print(f"3. Implement it in crypto-price-historical function")
print(f"\nIf no method worked, ask your developer for more details about")
print(f"exactly how they used the 'resolution' option to find prices.")