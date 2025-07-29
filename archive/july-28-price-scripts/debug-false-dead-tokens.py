import json
import urllib.request
from datetime import datetime

print("=== Debugging False Dead Token Detection ===")
print(f"Date: {datetime.now()}")

# Test the exact API call that crypto-poller is making
test_cases = [
    {
        "name": "$OPTI",
        "network": "ethereum",
        "pool": "0xd23EA6834ea57A65797303AECaDF74eDff9FA095",
        "contract": "0x05E651Fe74f82598f52Da6C5761C02b7a8f56fCa"
    },
    {
        "name": "HONOKA", 
        "network": "ethereum",
        "pool": "0x0Ee732251ce31fF8349561E1408d7828B86FB5Dd",
        "contract": "0x8d9779A08A5E38e8b5A28bd31E50b8cd3D238Ed8"
    }
]

def test_gecko_api_call(network, pool_address, token_name):
    """Test the exact API call that crypto-poller makes"""
    url = f"https://api.geckoterminal.com/api/v2/networks/{network}/pools/{pool_address}"
    
    print(f"\n--- Testing {token_name} ---")
    print(f"URL: {url}")
    
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0')
    
    try:
        response = urllib.request.urlopen(req)
        print(f"✅ Response Status: {response.getcode()}")
        
        data = json.loads(response.read().decode())
        
        if data.get('data'):
            attrs = data['data']['attributes']
            price_usd = attrs.get('base_token_price_usd')
            
            print(f"✅ Pool data found!")
            print(f"   Pool name: {attrs.get('name', 'Unknown')}")
            print(f"   Base token price USD: {price_usd}")
            print(f"   Reserve USD: ${float(attrs.get('reserve_in_usd', 0)):,.2f}")
            
            if price_usd:
                price = float(price_usd)
                print(f"   💰 PRICE: ${price:.8f}")
                
                if price > 0:
                    print(f"   🎯 This should be GECKO_LIVE, not DEAD_TOKEN!")
                    return price
                else:
                    print(f"   ❌ Price is 0 - correctly marked as dead")
                    return None
            else:
                print(f"   ❌ No base_token_price_usd field")
                return None
        else:
            print(f"❌ No data field in response")
            return None
            
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error: {e.code} - {e.reason}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

# Test both tokens
results = []
for case in test_cases:
    price = test_gecko_api_call(case["network"], case["pool"], case["name"])
    results.append({
        "name": case["name"],
        "price": price,
        "should_be_live": price is not None and price > 0
    })

print(f"\n{'='*60}")
print(f"SUMMARY:")

for result in results:
    status = "🎯 SHOULD BE LIVE" if result["should_be_live"] else "💀 Correctly dead"
    price_str = f"${result['price']:.8f}" if result["price"] else "No price"
    print(f"{result['name']}: {price_str} - {status}")

if any(r["should_be_live"] for r in results):
    print(f"\n🔍 ISSUE FOUND: Some tokens should be live but are marked as dead!")
    print(f"Need to debug the fetchCurrentPrice() function in crypto-poller")
else:
    print(f"\n✅ All tokens correctly identified as dead")

print(f"\n🛠️  Next step: Check the exact logic in crypto-poller fetchCurrentPrice()")