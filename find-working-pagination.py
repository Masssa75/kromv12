#!/usr/bin/env python3
"""
Test all possible pagination methods for KROM API
Keep trying until we find one that returns different data
"""

import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

KROM_API_TOKEN = os.getenv("KROM_API_TOKEN")
headers = {'Authorization': f'Bearer {KROM_API_TOKEN}'}

print("Testing ALL pagination methods for KROM API...")
print("=" * 80)

# First get initial batch to compare against
print("\n1. Getting initial batch for comparison...")
base_url = "https://krom.one/api/v1/calls?limit=10"
response = requests.get(base_url, headers=headers)
if response.status_code != 200:
    print(f"Error: {response.status_code}")
    exit(1)

initial_calls = response.json()
initial_ids = [c.get('id') for c in initial_calls[:5]]
print(f"Got {len(initial_calls)} calls")
print(f"First 5 IDs: {initial_ids}")

# Get values to use for pagination
last_call = initial_calls[-1]
last_id = last_call.get('id')
last_timestamp = last_call.get('timestamp')
last_trade_timestamp = last_call.get('trade', {}).get('buyTimestamp')

print(f"\nLast call details:")
print(f"  ID: {last_id}")
print(f"  Timestamp: {last_timestamp}")
print(f"  Trade timestamp: {last_trade_timestamp}")

# Test all possible pagination parameters
test_params = [
    # ID-based
    ('before', last_id),
    ('beforeId', last_id),
    ('after', last_id),
    ('afterId', last_id),
    ('lastId', last_id),
    ('last_id', last_id),
    ('cursor', last_id),
    ('next', last_id),
    ('from', last_id),
    ('fromId', last_id),
    
    # Timestamp-based (if we have timestamps)
    ('beforeTimestamp', last_timestamp),
    ('before_timestamp', last_timestamp),
    ('beforetimestamp', last_timestamp),
    ('timestamp', last_timestamp),
    ('until', last_timestamp),
    ('before_ts', last_timestamp),
    
    # Trade timestamp-based
    ('beforeTimestamp', last_trade_timestamp),
    ('before_timestamp', last_trade_timestamp),
    ('beforetimestamp', last_trade_timestamp),
    
    # Offset/page based
    ('offset', '10'),
    ('offset', '100'),
    ('offset', '200'),
    ('skip', '10'),
    ('skip', '100'),
    ('page', '2'),
    ('page', '3'),
    ('start', '10'),
    ('start', '100'),
    
    # Other possibilities
    ('limit', '10&offset=10'),  # Try combining
    ('limit', '10&skip=10'),
    ('_start', '10'),
    ('_offset', '10'),
]

print(f"\n\nTesting {len(test_params)} different parameter combinations...")
print("-" * 80)

working_params = []

for param_name, param_value in test_params:
    if param_value is None:
        continue
        
    url = f"{base_url}&{param_name}={param_value}"
    print(f"\nTesting: {param_name}={param_value}")
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            calls = response.json()
            
            if len(calls) > 0:
                new_ids = [c.get('id') for c in calls[:5]]
                
                # Check if we got different data
                if new_ids != initial_ids:
                    print(f"  ✓ SUCCESS! Got {len(calls)} different calls")
                    print(f"  New IDs: {new_ids[:3]}...")
                    working_params.append((param_name, param_value))
                    
                    # Test if we can go deeper
                    if len(calls) > 0:
                        next_last = calls[-1].get('id')
                        url2 = f"{base_url}&{param_name}={next_last}"
                        response2 = requests.get(url2, headers=headers, timeout=10)
                        if response2.status_code == 200:
                            calls2 = response2.json()
                            if len(calls2) > 0 and calls2[0].get('id') != calls[0].get('id'):
                                print(f"  ✓✓ CONFIRMED! Can paginate multiple times!")
                else:
                    print(f"  ✗ Got same {len(calls)} calls")
            else:
                print(f"  ✗ Got 0 calls")
        else:
            print(f"  ✗ Error: {response.status_code}")
            
    except Exception as e:
        print(f"  ✗ Exception: {e}")
    
    time.sleep(0.2)  # Be nice to the API

# Also test some alternative endpoints
print("\n\nTesting alternative endpoints...")
print("-" * 80)

alt_endpoints = [
    "https://krom.one/api/v1/calls/all",
    "https://krom.one/api/v1/calls/history",
    "https://krom.one/api/v1/calls/archive",
    "https://krom.one/api/v2/calls",
    "https://api.krom.one/v1/calls",
    "https://api.krom.app/v1/calls",
]

for endpoint in alt_endpoints:
    print(f"\nTesting: {endpoint}")
    try:
        response = requests.get(f"{endpoint}?limit=10", headers=headers, timeout=10)
        if response.status_code == 200:
            print(f"  ✓ Endpoint exists! Status: {response.status_code}")
        else:
            print(f"  ✗ Status: {response.status_code}")
    except Exception as e:
        print(f"  ✗ Exception: {e}")

# Summary
print("\n" + "=" * 80)
print("SUMMARY")
print("=" * 80)

if working_params:
    print(f"\nFound {len(working_params)} working pagination method(s):")
    for param, value in working_params:
        print(f"  - {param}={value}")
else:
    print("\nNo working pagination methods found.")
    print("\nThe API might:")
    print("  1. Only return the most recent 100 calls")
    print("  2. Require a different authentication method for historical data")
    print("  3. Use a completely different endpoint for historical data")
    print("  4. Require a paid/premium API key for full access")

print("\nYou mentioned someone else was able to get 100K+ calls.")
print("Can you ask them:")
print("  - What exact API endpoint they used?")
print("  - What pagination parameters they used?")
print("  - If they needed special API permissions?")