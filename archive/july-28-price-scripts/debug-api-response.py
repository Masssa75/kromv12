#\!/usr/bin/env python3
import json
import urllib.request

print("=== Debugging API Response for Oldest Tokens ===")
print()

# Test the analyzed endpoint for the oldest tokens
url = "https://lively-torrone-8199e0.netlify.app/api/analyzed?limit=5&offset=0&sortBy=created_at&sortOrder=asc"

req = urllib.request.Request(url)
req.add_header('Accept', 'application/json')

try:
    response = urllib.request.urlopen(req)
    data = json.loads(response.read().decode())
    
    print(f"API returned {len(data.get('results', []))} results")
    print()
    
    # Pretty print the full first result
    if data.get('results'):
        first = data['results'][0]
        print("First result (BIP177):")
        print(f"  ticker: {first.get('token')}")
        print(f"  price_at_call: {first.get('price_at_call')}")
        print(f"  Type of price_at_call: {type(first.get('price_at_call'))}")
        print()
        print("All price-related fields:")
        for key, value in first.items():
            if 'price' in key.lower() or 'roi' in key.lower() or 'market_cap' in key.lower() or 'fdv' in key.lower():
                print(f"  {key}: {value} (type: {type(value).__name__})")
        
except Exception as e:
    print(f"Error calling API: {e}")

