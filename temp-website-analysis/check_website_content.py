#!/usr/bin/env python3
"""
Check what we're actually getting from websites
"""

import requests

def check_website(url):
    """
    See what the website returns
    """
    print(f"\n{'='*60}")
    print(f"Checking: {url}")
    print("="*60)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'unknown')}")
        print(f"Size: {len(response.text)} bytes")
        
        # Show first 500 chars
        print(f"\nFirst 500 characters:")
        print("-" * 40)
        print(response.text[:500])
        
        # Check if it's a JavaScript app
        if 'id="__next"' in response.text or 'id="root"' in response.text:
            print("\n⚠️  This is a client-side rendered app (React/Next.js)")
            print("The actual content is loaded by JavaScript")
            print("Would need Selenium or Playwright to get full content")
        
        # Check for redirects
        if response.history:
            print(f"\n⚠️  Redirected through: {[r.url for r in response.history]}")
            
    except Exception as e:
        print(f"Error: {e}")

# Check the problematic sites
sites = [
    'https://vocalad.ai/',
    'https://www.tren.finance/',
    'https://www.gradient.trade/'
]

for site in sites:
    check_website(site)