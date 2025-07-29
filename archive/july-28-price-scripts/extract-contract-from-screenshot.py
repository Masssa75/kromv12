#!/usr/bin/env python3
import json
import urllib.request

print("=== Extracting Contract Address from Screenshot ===")
print()

# From the screenshot I can see the URL shows a pool address
# geckoterminal.com/eth/pools/0xd23ea6834ea57a65797303aecadf74edff9fa095
# This suggests the pool DOES exist on GeckoTerminal

screenshot_pool = "0xd23ea6834ea57a65797303aecadf74edff9fa095"
print(f"Pool from screenshot: {screenshot_pool}")
print(f"KROM pool address:    0xd23EA6834ea57A65797303AECaDF74eDff9FA095")
print()

# These look the same! Let me test the direct pool call
url = f"https://api.geckoterminal.com/api/v2/networks/ethereum/pools/{screenshot_pool}"
print(f"Testing direct pool API call:")
print(f"URL: {url}")
print()

req = urllib.request.Request(url)
req.add_header('User-Agent', 'Mozilla/5.0')

try:
    response = urllib.request.urlopen(req)
    data = json.loads(response.read().decode())
    
    if data.get('data'):
        attrs = data['data']['attributes']
        print("✅ SUCCESS! Pool data found:")
        print(f"   Pool name: {attrs.get('name', 'Unknown')}")
        print(f"   Base token price USD: {attrs.get('base_token_price_usd')}")
        print(f"   Reserve USD: ${float(attrs.get('reserve_in_usd', 0)):,.2f}")
        
        # Get token info
        base_token = attrs.get('base_token', {})
        print(f"   Token symbol: {base_token.get('symbol', 'Unknown')}")
        print(f"   Token address: {base_token.get('address', 'Unknown')}")
        
        price_usd = attrs.get('base_token_price_usd')
        if price_usd:
            price = float(price_usd)
            print(f"   💰 CURRENT PRICE: ${price:.8f}")
            
            if price > 0:
                print("   🎯 This token is ALIVE and should be GECKO_LIVE!")
                print("   ❌ There's a bug in the crypto-poller fetchCurrentPrice function")
            else:
                print("   💀 Price is 0 - token might be dead")
        else:
            print("   ❌ No price data available")
    else:
        print("❌ No data field in response")
        
except urllib.error.HTTPError as e:
    print(f"❌ HTTP Error: {e.code} - {e.reason}")
    print("This matches what crypto-poller is seeing!")
except Exception as e:
    print(f"❌ Error: {e}")

print()
print("=== Analysis ===")
print("If the screenshot shows trading but API returns 404:")
print("1. Maybe different pool address format/case sensitivity")
print("2. Maybe API has temporary issues")
print("3. Maybe screenshot is from different source than API")
print("4. Maybe we need different headers/authentication")