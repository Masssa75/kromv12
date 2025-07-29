#!/usr/bin/env python3
"""Check if analysis_reasoning field is populated in new and old records"""

import os
import requests
from datetime import datetime

# Load environment variables
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

if not url or not key:
    with open('.env', 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                k, v = line.strip().split('=', 1)
                if k == 'SUPABASE_URL' and not url:
                    url = v.strip().strip('"')
                elif k == 'SUPABASE_SERVICE_ROLE_KEY' and not key:
                    key = v.strip().strip('"')

headers = {
    'apikey': key,
    'Authorization': f'Bearer {key}',
    'Content-Type': 'application/json'
}

# Check records analyzed after our fix (after 2025-07-29T01:35:00)
print('Checking recently analyzed calls (after our cron fix)...')
response = requests.get(
    f'{url}/rest/v1/crypto_calls',
    headers=headers,
    params={
        'select': 'ticker,analyzed_at,analysis_score,analysis_reasoning,analysis_model',
        'analyzed_at': 'gte.2025-07-29T01:35:00',
        'order': 'analyzed_at.desc',
        'limit': '10'
    }
)

recent_calls = response.json()
print(f'\nFound {len(recent_calls)} recently analyzed calls:')
for call in recent_calls[:5]:  # Show first 5
    reasoning = call.get('analysis_reasoning')
    has_reasoning = 'YES' if reasoning else 'NO'
    print(f'{call["ticker"]:10} - Score: {call.get("analysis_score", "NULL"):2} - Has reasoning: {has_reasoning} - Model: {call.get("analysis_model", "Unknown")}')
    if has_reasoning == 'YES':
        print(f'   Reasoning preview: {reasoning[:100]}...')

# Check the 69 fixed records
print('\n\nChecking the 69 fixed records (with TRASH/BASIC/SOLID tiers)...')
response2 = requests.get(
    f'{url}/rest/v1/crypto_calls',
    headers=headers,
    params={
        'select': 'ticker,analyzed_at,analysis_score,analysis_reasoning,analysis_tier',
        'analyzed_at': 'not.is.null',
        'analysis_reasoning': 'is.null',
        'analysis_tier': 'in.(TRASH,BASIC,SOLID,ALPHA)',
        'limit': '5'
    }
)

fixed_calls = response2.json()
print(f'Found {len(fixed_calls)} fixed records with null reasoning:')
for call in fixed_calls:
    print(f'{call["ticker"]:10} - Score: {call.get("analysis_score", "NULL")} - Tier: {call.get("analysis_tier", "NULL")} - Reasoning: NULL')

# Also check AIR token specifically
print('\n\nChecking AIR token specifically...')
response3 = requests.get(
    f'{url}/rest/v1/crypto_calls',
    headers=headers,
    params={
        'select': 'ticker,analyzed_at,analysis_score,analysis_reasoning,analysis_tier,analysis_model',
        'ticker': 'eq.AIR',
        'limit': '1'
    }
)

air_token = response3.json()
if air_token:
    air = air_token[0]
    print(f'AIR token status:')
    print(f'  Score: {air.get("analysis_score")}')
    print(f'  Tier: {air.get("analysis_tier")}')
    print(f'  Model: {air.get("analysis_model")}')
    print(f'  Has reasoning: {"YES" if air.get("analysis_reasoning") else "NO"}')
    print(f'  Analyzed at: {air.get("analyzed_at")}')