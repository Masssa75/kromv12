#!/usr/bin/env python3
"""Test which API is failing in the cron jobs"""

import os
import requests
import json

# Load environment variables
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
openrouter_key = os.environ.get('OPEN_ROUTER_API_KEY')
anthropic_key = os.environ.get('ANTHROPIC_API_KEY')

if not url or not key:
    with open('.env', 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                k, v = line.strip().split('=', 1)
                if k == 'SUPABASE_URL' and not url:
                    url = v.strip().strip('"')
                elif k == 'SUPABASE_SERVICE_ROLE_KEY' and not key:
                    key = v.strip().strip('"')
                elif k == 'OPEN_ROUTER_API_KEY' and not openrouter_key:
                    openrouter_key = v.strip().strip('"')
                elif k == 'ANTHROPIC_API_KEY' and not anthropic_key:
                    anthropic_key = v.strip().strip('"')

print('INVESTIGATING API FAILURES')
print('=' * 35)

# Check environment variables
print('1. Checking API keys...')
print(f'   SUPABASE_URL: {"✓" if url else "✗"}')
print(f'   SUPABASE_SERVICE_ROLE_KEY: {"✓" if key else "✗"}')
print(f'   OPEN_ROUTER_API_KEY: {"✓" if openrouter_key else "✗"}')
print(f'   ANTHROPIC_API_KEY: {"✓" if anthropic_key else "✗"}')

# Test OpenRouter API directly
print('\n2. Testing OpenRouter API directly...')
if openrouter_key:
    try:
        openrouter_response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {openrouter_key}',
            },
            json={
                'model': 'moonshotai/kimi-k2',
                'messages': [
                    {'role': 'user', 'content': 'Test message - just say "API works"'}
                ],
                'temperature': 0,
                'max_tokens': 10
            },
            timeout=10
        )
        
        print(f'   Status: {openrouter_response.status_code}')
        if openrouter_response.status_code == 200:
            result = openrouter_response.json()
            print(f'   Response: {result.get("choices", [{}])[0].get("message", {}).get("content", "No content")}')
        else:
            print(f'   Error: {openrouter_response.text}')
    except Exception as e:
        print(f'   Exception: {e}')
else:
    print('   OPEN_ROUTER_API_KEY not found')

# Test Supabase connection
print('\n3. Testing Supabase connection...')
try:
    headers_supabase = {
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json'
    }
    
    supabase_response = requests.get(
        f'{url}/rest/v1/crypto_calls',
        headers=headers_supabase,
        params={'select': 'count', 'limit': '1'},
        timeout=10
    )
    
    print(f'   Status: {supabase_response.status_code}')
    if supabase_response.status_code == 200:
        print('   ✓ Supabase connection works')
    else:
        print(f'   Error: {supabase_response.text}')
except Exception as e:
    print(f'   Exception: {e}')

# Test the analyze endpoint with minimal payload
print('\n4. Testing /api/analyze endpoint...')
try:
    analyze_response = requests.post(
        'https://lively-torrone-8199e0.netlify.app/api/analyze',
        headers={'Content-Type': 'application/json'},
        json={'limit': 1, 'model': 'moonshotai/kimi-k2'},
        timeout=30
    )
    
    print(f'   Status: {analyze_response.status_code}')
    if analyze_response.status_code == 200:
        result = analyze_response.json()
        print(f'   Analyzed: {result.get("analyzed", 0)} calls')
        if result.get("errors"):
            print(f'   Errors: {len(result["errors"])}')
            print(f'   First error: {result["errors"][0] if result["errors"] else "None"}')
    else:
        print(f'   Error response: {analyze_response.text}')
except Exception as e:
    print(f'   Exception: {e}')

print('\n5. Summary:')
print('   The issue is likely one of:')
print('   - API rate limiting (429 errors)')
print('   - Missing/invalid API keys in Netlify')
print('   - Network timeouts')
print('   - Model-specific issues with kimi-k2')