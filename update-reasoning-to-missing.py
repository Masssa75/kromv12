#!/usr/bin/env python3
"""Update records with generic reasoning to indicate reasoning is missing"""

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

print("Fetching records with generic reasoning text...")

# Generic reasoning texts to look for
generic_texts = [
    "This token demonstrates exceptional characteristics with strong community engagement",
    "This token shows solid fundamentals with active development",
    "This token displays basic legitimacy with some genuine activity",
    "This token exhibits characteristics typical of low-quality projects"
]

# Get records that have one of the generic reasoning texts
all_records = []
for text in generic_texts:
    response = requests.get(
        f"{url}/rest/v1/crypto_calls",
        headers=headers,
        params={
            'select': 'id,ticker,analysis_reasoning',
            'analysis_reasoning': f'like.{text[:50]}*',  # Match beginning of text
        }
    )
    records = response.json()
    all_records.extend(records)

# Remove duplicates based on id
unique_records = {r['id']: r for r in all_records}.values()
print(f"Found {len(unique_records)} records with generic reasoning")

# Update message
missing_reasoning = "Analysis reasoning not available. This token was analyzed before detailed reasoning was implemented."

fixed = 0
for record in unique_records:
    # Update the record
    update_response = requests.patch(
        f"{url}/rest/v1/crypto_calls",
        headers=headers,
        params={'id': f'eq.{record["id"]}'},
        json={
            'analysis_reasoning': missing_reasoning
        }
    )
    
    if update_response.status_code == 204:
        fixed += 1
        print(f"Updated {record['ticker']} - set reasoning to 'missing' message")
    else:
        print(f"Failed to update {record['ticker']}: {update_response.status_code}")

print(f"\nUpdated {fixed} records to indicate missing reasoning")