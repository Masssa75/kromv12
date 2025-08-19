#!/usr/bin/env python3
"""Debug the batch script issue"""

import os
import sys
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

print("Starting debug...")
print(f"Current directory: {os.getcwd()}")

# Test Supabase connection
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

print(f"Supabase URL: {supabase_url[:30]}..." if supabase_url else "Supabase URL not found")
print(f"Service key: {supabase_key[:30]}..." if supabase_key else "Service key not found")

if not supabase_url or not supabase_key:
    print("ERROR: Missing environment variables!")
    sys.exit(1)

print("\n📡 Testing Supabase connection...")

try:
    response = requests.get(
        f'{supabase_url}/rest/v1/crypto_calls',
        headers={
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}'
        },
        params={
            'select': 'ticker,website_url',
            'limit': '5'
        },
        timeout=10
    )
    
    print(f"Response status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ Got {len(data)} tokens")
        for token in data[:3]:
            print(f"  - {token['ticker']}: {token.get('website_url', 'No URL')}")
    else:
        print(f"❌ Error: {response.text[:200]}")
        
except Exception as e:
    print(f"❌ Exception: {e}")

print("\nDebug complete.")