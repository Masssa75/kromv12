#!/usr/bin/env python3
"""Fix X analysis records that have tier but no score"""

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

print("Fetching X analysis records with tier but no score...")

# Get records that need fixing
response = requests.get(
    f"{url}/rest/v1/crypto_calls",
    headers=headers,
    params={
        'select': 'id,ticker,x_analysis_tier,x_analyzed_at',
        'x_analysis_tier': 'not.is.null',
        'x_analysis_score': 'is.null',
        'order': 'x_analyzed_at.desc'
    }
)

records = response.json()
print(f"Found {len(records)} X analysis records to fix")

# Tier to score mapping (same as call analysis)
tier_to_score = {
    'ALPHA': 9,
    'SOLID': 7,
    'BASIC': 5,
    'TRASH': 2
}

fixed = 0
for record in records:
    # Determine score based on tier
    tier = record.get('x_analysis_tier', 'TRASH')
    score = tier_to_score.get(tier, 2)
    
    # Update the record
    update_response = requests.patch(
        f"{url}/rest/v1/crypto_calls",
        headers=headers,
        params={'id': f'eq.{record["id"]}'},
        json={
            'x_analysis_score': score,
            'x_analysis_model': 'claude-3-haiku-20240307',  # Original model
            'x_legitimacy_factor': 'High' if score >= 8 else 'Medium' if score >= 5 else 'Low',
            'x_analysis_token_type': 'meme',  # Default since we don't have the original
            'x_analysis_reasoning': 'Analysis reasoning not available. This token was analyzed before detailed reasoning was implemented.'
        }
    )
    
    if update_response.status_code == 204:
        fixed += 1
        print(f"Fixed {record['ticker']} - set X score to {score} (based on {tier})")
    else:
        print(f"Failed to fix {record['ticker']}: {update_response.status_code}")

print(f"\nFixed {fixed} X analysis records")