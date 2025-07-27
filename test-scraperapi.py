#!/usr/bin/env python3

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get API key
SCRAPERAPI_KEY = os.getenv('SCRAPERAPI_KEY')

if not SCRAPERAPI_KEY:
    print("❌ No SCRAPERAPI_KEY found in .env file!")
    exit(1)

print(f"Testing ScraperAPI with key: {SCRAPERAPI_KEY[:10]}...")

# Test 1: Check account status
print("\n1. Checking account status...")
status_url = f"https://api.scraperapi.com/account?api_key={SCRAPERAPI_KEY}"
try:
    response = requests.get(status_url)
    print(f"   Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ Account active!")
        print(f"   - Plan: {data.get('planName', 'Unknown')}")
        print(f"   - Requests used: {data.get('requestCount', 0):,}")
        print(f"   - Requests limit: {data.get('requestLimit', 0):,}")
        print(f"   - Remaining: {data.get('requestLimit', 0) - data.get('requestCount', 0):,}")
    else:
        print(f"   ❌ Error: {response.text}")
except Exception as e:
    print(f"   ❌ Error checking account: {e}")

# Test 2: Try to fetch Nitter
print("\n2. Testing Nitter fetch...")
test_contract = "4X2uNTWfSEu5YdtPzqorFGcu5VXBu62nfYv2ys8wpump"
target_url = f"https://nitter.net/search?q={test_contract}&f=tweets"
scraper_url = f"https://api.scraperapi.com/?api_key={SCRAPERAPI_KEY}&url={requests.utils.quote(target_url)}"

try:
    response = requests.get(scraper_url)
    print(f"   Status Code: {response.status_code}")
    if response.status_code == 200:
        print(f"   ✅ Successfully fetched Nitter! Response length: {len(response.text)} chars")
        # Check if we got actual content
        if "tweet-content" in response.text:
            print("   ✅ Found tweet content in response")
        else:
            print("   ⚠️  No tweet content found (might be no tweets for this contract)")
    elif response.status_code == 403:
        print(f"   ❌ 403 Forbidden - API key is invalid or quota exceeded")
        print(f"   Response: {response.text[:200]}")
    else:
        print(f"   ❌ Error: {response.text[:200]}")
except Exception as e:
    print(f"   ❌ Error fetching: {e}")

# Test 3: Try alternative - direct Nitter fetch (no proxy)
print("\n3. Testing direct Nitter access (without ScraperAPI)...")
try:
    response = requests.get(target_url, timeout=10)
    print(f"   Status Code: {response.status_code}")
    if response.status_code == 200:
        print(f"   ✅ Direct Nitter access works! Response length: {len(response.text)} chars")
        if "tweet-content" in response.text:
            print("   ✅ Found tweet content in response")
    else:
        print(f"   ❌ Direct access failed with status: {response.status_code}")
except Exception as e:
    print(f"   ❌ Direct access blocked or timeout: {e}")

print("\n" + "="*60)
print("DIAGNOSIS:")
print("="*60)

if SCRAPERAPI_KEY:
    print(f"✓ ScraperAPI key found: {SCRAPERAPI_KEY[:10]}...")
    print("\nIf you're getting 403 errors, check:")
    print("1. Is your API key valid? (check ScraperAPI dashboard)")
    print("2. Have you exceeded the free tier limit (1000 requests/month)?")
    print("3. Try getting a new API key from https://www.scraperapi.com/")
    print("\nAlternative solutions:")
    print("- Use a different proxy service (Scrapfly, ProxyCrawl, etc.)")
    print("- Try direct Nitter access if it works")
    print("- Use a different Nitter instance (nitter.poast.org, nitter.net, etc.)")