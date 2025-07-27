#!/usr/bin/env python3
"""Direct test of database storage issue"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Simplified get_krom_calls for testing
def test_get_krom_calls():
    krom_token = os.getenv("KROM_API_TOKEN")
    url = f"https://krom.one/api/v1/calls?limit=1"
    headers = {'Authorization': f'Bearer {krom_token}'}
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        calls = response.json()
        print(f"Raw API response type: {type(calls)}")
        if isinstance(calls, list):
            print(f"Response is a list with {len(calls)} items")
            if calls:
                print(f"First item type: {type(calls[0])}")
                print(f"First item keys: {calls[0].keys()}")
                # Check the structure
                first_call = calls[0]
                print(f"\nCall structure:")
                print(f"  id: {first_call.get('id')}")
                print(f"  token: {type(first_call.get('token'))}")
                print(f"  trade: {type(first_call.get('trade'))}")
                print(f"  group: {type(first_call.get('group'))}")
        else:
            print(f"Response is not a list: {calls}")

print("Testing KROM API response structure...")
test_get_krom_calls()