#!/usr/bin/env python3
"""Clear the fake call analysis data so cron can reprocess properly"""

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

print("Finding call analysis records with generic reasoning...")

# Get records that have the generic reasoning text
response = requests.get(
    f"{url}/rest/v1/crypto_calls",
    headers=headers,
    params={
        'select': 'id,ticker,analysis_score,analysis_tier',
        'analysis_reasoning': 'eq.Analysis reasoning not available. This token was analyzed before detailed reasoning was implemented.',
        'order': 'analyzed_at.desc'
    }
)

records = response.json()
print(f"Found {len(records)} call analysis records to clear")

cleared = 0
for record in records:
    # Clear all the new analysis fields but keep the old tier
    update_response = requests.patch(
        f"{url}/rest/v1/crypto_calls",
        headers=headers,
        params={'id': f'eq.{record["id"]}'},
        json={
            'analysis_score': None,
            'analysis_model': None,
            'analysis_legitimacy_factor': None,
            'analysis_token_type': None,
            'analysis_reasoning': None,
            'analyzed_at': None,
            'analysis_reanalyzed_at': None
            # Keep analysis_tier as it's from the old system
        }
    )
    
    if update_response.status_code == 204:
        cleared += 1
        print(f"Cleared {record['ticker']} - removed fake call analysis data")
    else:
        print(f"Failed to clear {record['ticker']}: {update_response.status_code}")

print(f"\nCleared {cleared} call analysis records")
print("These will now be picked up by the cron job for proper analysis")