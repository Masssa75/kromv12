#!/usr/bin/env python3
"""
Debug the OpenRouter API issue
"""

import requests
import json

# API key from the .env file (OPEN_ROUTER_API_KEY - Updated Aug 19, 2025)
api_key = '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'

# Test with a simple prompt
prompt = "Just respond with: {'test': 'success'}"

print("Testing OpenRouter API...")
print(f"API Key: {api_key[:20]}...")

response = requests.post(
    'https://openrouter.ai/api/v1/chat/completions',
    headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}',
    },
    json={
        'model': 'moonshotai/kimi-k2',
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.1,
        'max_tokens': 100
    },
    timeout=30
)

print(f"\nStatus Code: {response.status_code}")
print(f"Response Headers: {dict(response.headers)}")

if response.status_code == 200:
    print("\n✅ API call successful!")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2)}")
else:
    print("\n❌ API call failed!")
    print(f"Error Response: {response.text}")
    
    # Try to parse error
    try:
        error_data = response.json()
        print(f"\nError details:")
        print(f"  Type: {error_data.get('error', {}).get('type')}")
        print(f"  Message: {error_data.get('error', {}).get('message')}")
        print(f"  Code: {error_data.get('error', {}).get('code')}")
    except:
        pass