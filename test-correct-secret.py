#!/usr/bin/env python3
"""
Test cron endpoints with correct CRON_SECRET
"""

import requests

# Use the correct CRON_SECRET from Netlify
CRON_SECRET = 'rxnuzmLknGx0Okw2Te9db/8KkceZWhuKaHy6+Otm9FY='

print("🧪 TESTING CRON ENDPOINTS WITH CORRECT SECRET")
print("=" * 50)

endpoints = [
    {
        'name': 'Call Analysis',
        'url': 'https://lively-torrone-8199e0.netlify.app/api/cron/analyze'
    },
    {
        'name': 'X Analysis', 
        'url': 'https://lively-torrone-8199e0.netlify.app/api/cron/x-analyze'
    }
]

for endpoint in endpoints:
    print(f"\n📋 Testing {endpoint['name']}...")
    print(f"   URL: {endpoint['url']}")
    
    try:
        # Use GET request with correct auth parameter
        response = requests.get(
            endpoint['url'],
            params={'auth': CRON_SECRET},
            timeout=60  # Longer timeout for processing
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"   ✅ Success!")
                print(f"   Processed: {result.get('processed', 'N/A')}")
                print(f"   Total: {result.get('total', 'N/A')}")
                print(f"   Remaining: {result.get('remaining', 'N/A')}")
                print(f"   Duration: {result.get('duration', 'N/A')}")
                if result.get('errors', 0) > 0:
                    print(f"   Errors: {result.get('errors', 0)}")
            except:
                print(f"   ✅ Success (non-JSON response)")
                print(f"   Response: {response.text[:200]}")
        else:
            print(f"   ❌ Failed")
            print(f"   Error: {response.text[:300]}")
            
    except Exception as e:
        print(f"   ❌ Request failed: {str(e)}")

print("=" * 50)