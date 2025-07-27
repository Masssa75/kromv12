#!/usr/bin/env python3
"""
Debug script to test the calls API endpoint
Run this while the server is running to see what data is returned
"""

import requests
import json

# Test the API endpoint
url = "http://localhost:5001/api/calls"
params = {
    "page": 1,
    "per_page": 10
}

print("Testing calls API endpoint...")
print(f"URL: {url}")
print(f"Params: {params}")
print("-" * 50)

try:
    response = requests.get(url, params=params)
    print(f"Status Code: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    print("-" * 50)
    
    if response.status_code == 200:
        data = response.json()
        print("Response JSON:")
        print(json.dumps(data, indent=2))
        
        if 'calls' in data and len(data['calls']) > 0:
            print("\nFirst call structure:")
            print(json.dumps(data['calls'][0], indent=2))
        else:
            print("\nNo calls in response!")
    else:
        print(f"Error: {response.text}")
        
except Exception as e:
    print(f"Error making request: {e}")

# Also test the stats endpoint
print("\n" + "="*50 + "\n")
print("Testing stats endpoint...")
stats_url = "http://localhost:5001/api/stats"

try:
    response = requests.get(stats_url)
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        print("Stats response:")
        print(json.dumps(response.json(), indent=2))
except Exception as e:
    print(f"Error: {e}")