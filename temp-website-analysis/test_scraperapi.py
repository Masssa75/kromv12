#!/usr/bin/env python3
"""Test ScraperAPI"""

import requests

SCRAPERAPI_KEY = "43f3f4aa590f2d310b5a70d8a28e94a2"
url = "https://assino.xyz/"

print(f"Testing ScraperAPI with {url}")

api_url = "http://api.scraperapi.com"
params = {
    'api_key': SCRAPERAPI_KEY,
    'url': url,
    'render': 'true',
    'timeout': '20000'
}

print("Making request...")
try:
    response = requests.get(api_url, params=params, timeout=25)
    print(f"Status: {response.status_code}")
    print(f"Content length: {len(response.text)} characters")
    if response.status_code == 200:
        print("✅ ScraperAPI working!")
        print(f"First 500 chars: {response.text[:500]}")
    else:
        print(f"❌ Error: {response.text[:200]}")
except Exception as e:
    print(f"❌ Exception: {e}")