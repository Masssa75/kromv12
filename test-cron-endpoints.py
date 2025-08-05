#!/usr/bin/env python3
"""
Test cron endpoints manually with correct HTTP method
"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

CRON_SECRET = os.getenv('CRON_SECRET', 'a07066e62da04a115fde8f18813a931b16095bbaa2fac17dfd6cd0d9662ae30b')

print("🧪 TESTING CRON ENDPOINTS")
print("=" * 40)

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
        # Use GET request with auth parameter
        response = requests.get(
            endpoint['url'],
            params={'auth': CRON_SECRET},
            timeout=30
        )
        
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                result = response.json()
                print(f"   ✅ Success!")
                print(f"   Response: {result}")
            except:
                print(f"   ✅ Success (non-JSON response)")
                print(f"   Response: {response.text[:200]}")
        else:
            print(f"   ❌ Failed")
            print(f"   Error: {response.text[:200]}")
            
    except Exception as e:
        print(f"   ❌ Request failed: {str(e)}")

print("=" * 40)