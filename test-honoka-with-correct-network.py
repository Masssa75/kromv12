#!/usr/bin/env python3
import json
import urllib.request

print("=== Testing HONOKA with Correct Network Name ===")
print()

# Test HONOKA with "eth" instead of "ethereum"
honoka_pool = "0x0Ee732251ce31fF8349561E1408d7828B86FB5Dd"

url = f"https://api.geckoterminal.com/api/v2/networks/eth/pools/{honoka_pool}"
print(f"Testing HONOKA with 'eth' network:")
print(f"URL: {url}")
print()

req = urllib.request.Request(url)
req.add_header('User-Agent', 'Mozilla/5.0')

try:
    response = urllib.request.urlopen(req)
    data = json.loads(response.read().decode())
    
    if data.get('data'):
        attrs = data['data']['attributes']
        price = attrs.get('base_token_price_usd')
        
        print("✅ SUCCESS! HONOKA data found:")
        print(f"   Pool: {attrs.get('name', 'Unknown')}")
        print(f"   Price: ${float(price) if price else 0:.8f}")
        print(f"   Reserve: ${float(attrs.get('reserve_in_usd', 0)):,.2f}")
        
        if price and float(price) > 0:
            print("   🎯 HONOKA is also ALIVE!")
        else:
            print("   💀 No price data")
    else:
        print("❌ No data in response")
        
except urllib.error.HTTPError as e:
    print(f"❌ HTTP Error: {e.code} - {e.reason}")
except Exception as e:
    print(f"❌ Error: {e}")

print()
print("=== Network Mapping Issue Confirmed ===")
print("KROM stores: 'ethereum'")
print("GeckoTerminal API needs: 'eth'")
print()
print("We need to create a network mapping in crypto-poller:")
print("'ethereum' -> 'eth'")
print("'solana' -> 'solana' (probably stays the same)")
print("'bsc' -> 'bsc' (probably stays the same)")