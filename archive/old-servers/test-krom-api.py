#!/usr/bin/env python3
"""Test KROM API directly to see the data format"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def test_krom_api():
    token = os.getenv("KROM_API_TOKEN")
    if not token:
        print("No KROM API token found!")
        return
    
    url = "https://krom.one/api/v1/calls?limit=5"
    headers = {
        'Authorization': f'Bearer {token}'
    }
    
    print(f"Testing KROM API...")
    print(f"URL: {url}")
    print(f"Token: {token[:10]}...{token[-10:]}")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\nGot {len(data)} calls")
            
            # Print first call in detail
            if data and len(data) > 0:
                print("\nFirst call structure:")
                print(json.dumps(data[0], indent=2))
                
                # Show all available fields
                print("\nAvailable fields in first call:")
                for key in data[0].keys():
                    print(f"  - {key}: {type(data[0][key]).__name__}")
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_krom_api()