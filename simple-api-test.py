#!/usr/bin/env python3
"""
Simple test to check if the DexScreener API fix works
Just makes a request and prints the results
"""
import requests
import json

# Test the endpoint
url = 'http://localhost:5001/api/dexscreener/signals'
print(f"Testing: {url}")
print("-" * 50)

try:
    response = requests.get(url, timeout=30)
    data = response.json()
    
    if data.get('success'):
        summary = data.get('summary', {})
        print(f"✅ New Launches: {summary.get('new_launches', 0)}")
        print(f"✅ Volume Spikes: {summary.get('volume_spikes', 0)}")
        print(f"✅ Boosted Tokens: {summary.get('boosted_tokens', 0)}")
        
        # Show some examples
        signals = data.get('signals', {})
        if signals.get('new_launches'):
            print(f"\nExample new launch: {signals['new_launches'][0]['symbol']}")
        if signals.get('volume_spikes'):
            print(f"Example volume spike: {signals['volume_spikes'][0]['symbol']}")
            
        # Save full response
        with open('api-test-result.json', 'w') as f:
            json.dump(data, f, indent=2)
        print(f"\nFull response saved to api-test-result.json")
    else:
        print(f"❌ API returned error: {data}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    print("\nMake sure server is running:")
    print("python3 all-in-one-server.py")