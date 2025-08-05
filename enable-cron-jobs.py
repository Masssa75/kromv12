#!/usr/bin/env python3
"""
Enable the disabled cron jobs
"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

CRON_API_KEY = os.getenv('CRON_JOB_API')

headers = {
    'Authorization': f'Bearer {CRON_API_KEY}',
    'Content-Type': 'application/json'
}

def enable_job(job_id):
    """Enable a cron job"""
    url = f"https://api.cron-job.org/jobs/{job_id}"
    data = {'job': {'enabled': True}}
    response = requests.patch(url, headers=headers, json=data)
    response.raise_for_status()
    return response.json()

# Job IDs from the previous check
CALL_ANALYSIS_JOB_ID = "6380042"
X_ANALYSIS_JOB_ID = "6380045"

print("🔧 ENABLING CRON JOBS")
print("=" * 30)

try:
    # Enable Call Analysis job
    print(f"Enabling Call Analysis job (ID: {CALL_ANALYSIS_JOB_ID})...")
    result1 = enable_job(CALL_ANALYSIS_JOB_ID)
    print("✅ Call Analysis job enabled successfully")
    
    # Enable X Analysis job
    print(f"Enabling X Analysis job (ID: {X_ANALYSIS_JOB_ID})...")
    result2 = enable_job(X_ANALYSIS_JOB_ID)
    print("✅ X Analysis job enabled successfully")
    
    print("\n🎉 Both cron jobs are now enabled and should start processing!")
    print("📅 Expected schedule: Every minute for both jobs")
    print("⚡ Processing should resume within 1-2 minutes")
    
except Exception as e:
    print(f"❌ Error enabling cron jobs: {str(e)}")

print("=" * 30)