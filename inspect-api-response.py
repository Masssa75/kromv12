#!/usr/bin/env python3
"""Inspect full API response to see all available fields"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

KROM_API_TOKEN = os.getenv("KROM_API_TOKEN")
headers = {'Authorization': f'Bearer {KROM_API_TOKEN}'}

print("Fetching one call to inspect full data structure...")
response = requests.get("https://krom.one/api/v1/calls?limit=1", headers=headers)

if response.status_code == 200:
    calls = response.json()
    if calls:
        call = calls[0]
        
        # Save full response for inspection
        with open('sample-call-full.json', 'w') as f:
            json.dump(call, f, indent=2)
        
        print("\nFull call structure saved to: sample-call-full.json")
        print("\nTop-level keys:")
        for key in call.keys():
            print(f"  - {key}: {type(call[key]).__name__}")
            
        # Check nested structures
        if 'token' in call and isinstance(call['token'], dict):
            print("\nToken fields:")
            for key in call['token'].keys():
                print(f"  - token.{key}: {type(call['token'][key]).__name__}")
                
        if 'trade' in call and isinstance(call['trade'], dict):
            print("\nTrade fields:")
            for key in call['trade'].keys():
                print(f"  - trade.{key}: {type(call['trade'][key]).__name__}")
                
        if 'group' in call and isinstance(call['group'], dict):
            print("\nGroup fields:")
            for key in call['group'].keys():
                print(f"  - group.{key}: {type(call['group'][key]).__name__}")
                
        print("\n✓ Check sample-call-full.json for complete data")