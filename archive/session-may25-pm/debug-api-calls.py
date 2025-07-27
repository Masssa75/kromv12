#!/usr/bin/env python3
"""Debug script to check what the API returns with different offsets"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

KROM_API_TOKEN = os.getenv("KROM_API_TOKEN")
headers = {'Authorization': f'Bearer {KROM_API_TOKEN}'}

print("Checking API responses with different offsets...")
print("=" * 60)

# Test different offsets
for offset in [0, 100, 200, 500, 1000]:
    url = f"https://krom.one/api/v1/calls?limit=10&offset={offset}"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        calls = response.json()
        print(f"\nOffset {offset}: Got {len(calls)} calls")
        if calls:
            print(f"  First ID: {calls[0].get('id')}")
            print(f"  Last ID: {calls[-1].get('id')}")
            # Check if we've seen these IDs before
            ids = [c.get('id') for c in calls[:3]]
            print(f"  First 3 IDs: {ids}")
    else:
        print(f"\nOffset {offset}: Error {response.status_code}")