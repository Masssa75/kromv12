#!/usr/bin/env python3
"""Fix records that have analyzed_at but null analysis_score"""

import os
import requests
from datetime import datetime

# Load environment variables
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

if not url or not key:
    # Try loading from .env file
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

print("Fetching records with analyzed_at but null analysis_score...")

# Get records that need fixing
response = requests.get(
    f"{url}/rest/v1/crypto_calls",
    headers=headers,
    params={
        'select': 'id,ticker,analyzed_at,analysis_tier,analysis_model,analysis_legitimacy_factor,analysis_token_type',
        'analyzed_at': 'not.is.null',
        'analysis_score': 'is.null',
        'order': 'analyzed_at.desc'
    }
)

records = response.json()
print(f"Found {len(records)} records to fix")

# Tier to score mapping
tier_to_score = {
    'ALPHA': 9,
    'SOLID': 7,
    'BASIC': 5,
    'TRASH': 2
}

fixed = 0
for record in records:
    # Determine score based on tier
    tier = record.get('analysis_tier', 'TRASH')
    score = tier_to_score.get(tier, 2)
    
    # Update the record
    update_response = requests.patch(
        f"{url}/rest/v1/crypto_calls",
        headers=headers,
        params={'id': f'eq.{record["id"]}'},
        json={
            'analysis_score': score,
            'analysis_model': record.get('analysis_model') or 'moonshotai/kimi-k2',
            'analysis_legitimacy_factor': record.get('analysis_legitimacy_factor') or 'Low',
            'analysis_token_type': record.get('analysis_token_type') or 'meme'
        }
    )
    
    if update_response.status_code == 204:
        fixed += 1
        print(f"Fixed {record['ticker']} - set score to {score} (based on {tier})")
    else:
        print(f"Failed to fix {record['ticker']}: {update_response.status_code}")

print(f"\nFixed {fixed} records")