#\!/usr/bin/env python3
import json
import urllib.request

print("=== Testing krom-analysis-app API ===")
print()

# Test the analyzed endpoint
url = "https://lively-torrone-8199e0.netlify.app/api/analyzed?limit=10&offset=0&sortBy=created_at&sortOrder=asc"

req = urllib.request.Request(url)
req.add_header('Accept', 'application/json')

try:
    response = urllib.request.urlopen(req)
    data = json.loads(response.read().decode())
    
    print(f"API returned {len(data.get('results', []))} results")
    print()
    
    # Check first few results
    for i, result in enumerate(data.get('results', [])[:5]):
        print(f"{i+1}. {result.get('token', 'N/A')}")
        print(f"   price_at_call: {result.get('price_at_call', 'N/A')}")
        print(f"   raw_data exists: {'raw_data' in result}")
        if 'raw_data' in result and result['raw_data']:
            trade_data = result['raw_data'].get('trade', {})
            print(f"   KROM buyPrice: {trade_data.get('buyPrice', 'N/A')}")
        print()
        
except Exception as e:
    print(f"Error calling API: {e}")

