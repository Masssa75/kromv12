#!/usr/bin/env python3
"""
Update cron job URLs with correct CRON_SECRET
"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

CRON_API_KEY = os.getenv('CRON_JOB_API')
CORRECT_CRON_SECRET = 'rxnuzmLknGx0Okw2Te9db/8KkceZWhuKaHy6+Otm9FY='

headers = {
    'Authorization': f'Bearer {CRON_API_KEY}',
    'Content-Type': 'application/json'
}

def update_job(job_id, new_url):
    """Update a cron job URL"""
    url = f"https://api.cron-job.org/jobs/{job_id}"
    data = {'job': {'url': new_url}}
    response = requests.patch(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

# Job IDs and new URLs
jobs_to_update = [
    {
        'id': '6380042',
        'name': 'Call Analysis',
        'new_url': f'https://lively-torrone-8199e0.netlify.app/api/cron/analyze?auth={CORRECT_CRON_SECRET}'
    },
    {
        'id': '6380045', 
        'name': 'X Analysis',
        'new_url': f'https://lively-torrone-8199e0.netlify.app/api/cron/x-analyze?auth={CORRECT_CRON_SECRET}'
    }
]

print("🔧 UPDATING CRON JOB URLs")
print("=" * 35)

for job in jobs_to_update:
    try:
        print(f"\nUpdating {job['name']} (ID: {job['id']})...")
        print(f"New URL: {job['new_url']}")
        
        result = update_job(job['id'], job['new_url'])
        print("✅ URL updated successfully")
        
    except Exception as e:
        print(f"❌ Error updating {job['name']}: {str(e)}")

print("\n🎉 Cron job URLs updated with correct CRON_SECRET!")
print("⚡ Jobs should now run successfully every minute")
print("=" * 35)