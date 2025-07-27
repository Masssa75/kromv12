#!/usr/bin/env python3
"""Test script to debug database storage issue"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import all_in_one_server
get_krom_calls = all_in_one_server.get_krom_calls
download_krom_calls = all_in_one_server.download_krom_calls

# Test 1: Check what get_krom_calls returns
print("=== Testing get_krom_calls ===")
result = get_krom_calls(limit=1)
print(f"Success: {result.get('success')}")
print(f"Result keys: {result.keys()}")

if result.get('success'):
    data = result.get('data', {})
    print(f"Data type: {type(data)}")
    print(f"Data keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
    
    if isinstance(data, dict) and 'calls' in data:
        calls = data['calls']
        print(f"Calls type: {type(calls)}")
        print(f"Number of calls: {len(calls)}")
        if calls:
            print(f"First call type: {type(calls[0])}")
            print(f"First call keys: {calls[0].keys()}")
            print(f"First call id: {calls[0].get('id')}")

# Test 2: Try download_krom_calls
print("\n=== Testing download_krom_calls ===")
download_result = download_krom_calls(limit=1)
print(f"Download result: {download_result}")