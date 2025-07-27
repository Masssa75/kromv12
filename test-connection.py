#!/usr/bin/env python3
import os
import sys

# Simple .env reader
env_path = '.env'
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

# Get credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

print(f"SUPABASE_URL: {SUPABASE_URL}")
print(f"Has SERVICE_ROLE_KEY: {'Yes' if SUPABASE_SERVICE_ROLE_KEY else 'No'}")

try:
    import requests
    print("\n✓ requests library is available")
    
    # Test connection
    headers = {
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}'
    }
    
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=*&limit=1"
    print(f"\nTesting connection to: {url}")
    
    response = requests.get(url, headers=headers)
    print(f"Response status: {response.status_code}")
    
    if response.status_code == 200:
        print("✓ Successfully connected to Supabase")
        if response.text and response.text != '[]':
            print("✓ crypto_calls table has data")
        else:
            print("✓ crypto_calls table exists but is empty")
    else:
        print(f"✗ Error: {response.text}")
        
except ImportError:
    print("\n✗ requests library not installed")
    print("Install with: pip install requests")
except Exception as e:
    print(f"\n✗ Error: {str(e)}")