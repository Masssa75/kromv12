#!/usr/bin/env python3
import json
import urllib.request
import time

print("=== Investigating API vs Web Interface Mismatch ===")
print()

# The pool from your screenshot
pool_address = "0xd23ea6834ea57A65797303aecadf74edff9fa095"

print(f"Testing pool: {pool_address}")
print("From your screenshot URL: geckoterminal.com/eth/pools/{pool_address}")
print()

# Try different variations and approaches
test_cases = [
    {
        "name": "Direct pool call (original case)",
        "url": f"https://api.geckoterminal.com/api/v2/networks/ethereum/pools/{pool_address}"
    },
    {
        "name": "Direct pool call (uppercase)",
        "url": f"https://api.geckoterminal.com/api/v2/networks/ethereum/pools/{pool_address.upper()}"
    },
    {
        "name": "Direct pool call (eth instead of ethereum)",
        "url": f"https://api.geckoterminal.com/api/v2/networks/eth/pools/{pool_address}"
    },
    {
        "name": "Search all pools (first 20 chars of address)",
        "url": f"https://api.geckoterminal.com/api/v2/search/pools?query={pool_address[:20]}"
    }
]

for test in test_cases:
    print(f"--- {test['name']} ---")
    print(f"URL: {test['url']}")
    
    req = urllib.request.Request(test['url'])
    req.add_header('User-Agent', 'Mozilla/5.0')
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        
        print("✅ SUCCESS!")
        
        if 'data' in data:
            if isinstance(data['data'], list):
                print(f"   Found {len(data['data'])} results")
                for i, item in enumerate(data['data'][:3]):
                    attrs = item.get('attributes', {})
                    print(f"   Result {i+1}: {attrs.get('name', 'Unknown')}")
            else:
                attrs = data['data'].get('attributes', {})
                price = attrs.get('base_token_price_usd')
                print(f"   Pool: {attrs.get('name', 'Unknown')}")
                print(f"   Price: ${float(price) if price else 0:.8f}")
                
        print()
        
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error: {e.code} - {e.reason}")
        print()
    except Exception as e:
        print(f"❌ Error: {e}")
        print()
    
    time.sleep(0.5)

print("=== Key Questions ===")
print("1. Does the web interface use a different API endpoint?")
print("2. Does the web interface use different authentication?")
print("3. Is there a difference between 'ethereum' and 'eth' network names?")
print("4. Could this be a regional/geographic API restriction?")
print()
print("=== Next Steps ===")
print("If all API calls fail but web interface works:")
print("1. The web interface might use internal/private APIs")
print("2. We might need to use a different approach (web scraping)")
print("3. There could be rate limiting or IP blocking")
print("4. The public API might not have access to all pools")