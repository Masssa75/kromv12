#!/usr/bin/env python3
"""Test KROM API pagination to find the correct parameter"""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

KROM_API_TOKEN = os.getenv("KROM_API_TOKEN")
headers = {'Authorization': f'Bearer {KROM_API_TOKEN}'}

print("Testing KROM API pagination methods...")
print("=" * 60)

# First, get initial batch
print("\n1. Getting first batch...")
response = requests.get("https://krom.one/api/v1/calls?limit=10", headers=headers)
if response.status_code == 200:
    calls = response.json()
    print(f"Got {len(calls)} calls")
    
    if calls:
        first_call = calls[0]
        last_call = calls[-1]
        
        print(f"\nFirst call:")
        print(f"  ID: {first_call.get('id')}")
        print(f"  Timestamp: {first_call.get('timestamp')}")
        print(f"  Trade timestamp: {first_call.get('trade', {}).get('buyTimestamp')}")
        
        print(f"\nLast call:")
        print(f"  ID: {last_call.get('id')}")
        print(f"  Timestamp: {last_call.get('timestamp')}")
        print(f"  Trade timestamp: {last_call.get('trade', {}).get('buyTimestamp')}")
        
        # Test different pagination methods
        last_id = last_call.get('id')
        last_timestamp = last_call.get('trade', {}).get('buyTimestamp')
        
        print(f"\n2. Testing pagination with before={last_id}")
        test_url = f"https://krom.one/api/v1/calls?limit=10&before={last_id}"
        response = requests.get(test_url, headers=headers)
        if response.status_code == 200:
            next_calls = response.json()
            print(f"Got {len(next_calls)} calls")
            if next_calls and next_calls[0].get('id') != last_id:
                print("✓ Pagination with 'before' parameter works!")
                
        print(f"\n3. Testing pagination with beforeId={last_id}")
        test_url = f"https://krom.one/api/v1/calls?limit=10&beforeId={last_id}"
        response = requests.get(test_url, headers=headers)
        if response.status_code == 200:
            next_calls = response.json()
            print(f"Got {len(next_calls)} calls")
            if next_calls and next_calls[0].get('id') != last_id:
                print("✓ Pagination with 'beforeId' parameter works!")
                
        print(f"\n4. Testing pagination with offset=10")
        test_url = f"https://krom.one/api/v1/calls?limit=10&offset=10"
        response = requests.get(test_url, headers=headers)
        if response.status_code == 200:
            next_calls = response.json()
            print(f"Got {len(next_calls)} calls")
            if next_calls and next_calls[0].get('id') != last_id:
                print("✓ Pagination with 'offset' parameter works!")
                
        print(f"\n5. Testing pagination with page=2")
        test_url = f"https://krom.one/api/v1/calls?limit=10&page=2"
        response = requests.get(test_url, headers=headers)
        if response.status_code == 200:
            next_calls = response.json()
            print(f"Got {len(next_calls)} calls")
            if next_calls and next_calls[0].get('id') != last_id:
                print("✓ Pagination with 'page' parameter works!")
                
        # Check if there's a cursor or next link in response headers
        print(f"\n6. Checking response headers...")
        for key, value in response.headers.items():
            if 'link' in key.lower() or 'cursor' in key.lower() or 'next' in key.lower():
                print(f"  {key}: {value}")
                
else:
    print(f"Error: {response.status_code}")