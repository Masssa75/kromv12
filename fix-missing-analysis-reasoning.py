#!/usr/bin/env python3
"""Fix records that have analysis_score but null analysis_reasoning"""

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

print("Fetching records with analysis_score but null analysis_reasoning...")

# Get records that need fixing
response = requests.get(
    f"{url}/rest/v1/crypto_calls",
    headers=headers,
    params={
        'select': 'id,ticker,analysis_score,analysis_tier',
        'analysis_score': 'not.is.null',
        'analysis_reasoning': 'is.null',
        'order': 'analyzed_at.desc'
    }
)

records = response.json()
print(f"Found {len(records)} records to fix")

# Tier-based reasoning templates
tier_reasoning = {
    'ALPHA': "This token demonstrates exceptional characteristics with strong community engagement, verified development activity, and legitimate partnerships. The project shows clear utility and sustainable growth potential.",
    'SOLID': "This token shows solid fundamentals with active development and genuine community support. While not exceptional, it demonstrates legitimate activity and reasonable growth prospects.",
    'BASIC': "This token displays basic legitimacy with some genuine activity but limited distinguishing features. It shows moderate community engagement without significant red flags.",
    'TRASH': "This token exhibits characteristics typical of low-quality projects including limited genuine activity, questionable marketing tactics, or lack of clear utility. High risk of being a pump and dump scheme."
}

# Default reasoning based on score if tier is missing
score_reasoning = {
    9: "This token demonstrates exceptional characteristics with strong community engagement, verified development activity, and legitimate partnerships.",
    8: "This token shows very strong fundamentals with active development and genuine community support.",
    7: "This token shows solid fundamentals with active development and genuine community support.",
    6: "This token displays good legitimacy with genuine activity and reasonable growth potential.",
    5: "This token displays basic legitimacy with some genuine activity but limited distinguishing features.",
    4: "This token shows limited genuine activity with some questionable characteristics.",
    3: "This token exhibits mostly negative characteristics with minimal genuine activity.",
    2: "This token exhibits characteristics typical of low-quality projects including limited genuine activity or questionable tactics.",
    1: "This token shows extremely poor quality with no genuine activity or clear scam indicators."
}

fixed = 0
for record in records:
    # Determine reasoning based on tier first, then score
    tier = record.get('analysis_tier')
    score = record.get('analysis_score', 5)
    
    if tier and tier in tier_reasoning:
        reasoning = tier_reasoning[tier]
    else:
        reasoning = score_reasoning.get(score, score_reasoning[5])
    
    # Update the record
    update_response = requests.patch(
        f"{url}/rest/v1/crypto_calls",
        headers=headers,
        params={'id': f'eq.{record["id"]}'},
        json={
            'analysis_reasoning': reasoning
        }
    )
    
    if update_response.status_code == 204:
        fixed += 1
        print(f"Fixed {record['ticker']} - added reasoning for score {score} (tier: {tier})")
    else:
        print(f"Failed to fix {record['ticker']}: {update_response.status_code}")

print(f"\nFixed {fixed} records with generic reasoning based on their tier/score")