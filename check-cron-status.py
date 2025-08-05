#!/usr/bin/env python3
"""
Check cron job status using cron-job.org API
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

def get_cron_jobs():
    """Get all cron jobs"""
    url = "https://api.cron-job.org/jobs"
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_job_history(job_id, limit=5):
    """Get job execution history"""
    url = f"https://api.cron-job.org/jobs/{job_id}/history"
    params = {'limit': limit}
    response = requests.get(url, headers=headers, params=params)
    response.raise_for_status()
    return response.json()

print("🔍 CRON JOB STATUS CHECK")
print("=" * 50)

try:
    jobs_response = get_cron_jobs()
    jobs = jobs_response.get('jobs', [])
    
    # Find analysis-related jobs
    analysis_jobs = []
    for job in jobs:
        title = job.get('title', '').lower()
        if 'analysis' in title or 'analyze' in title:
            analysis_jobs.append(job)
    
    if not analysis_jobs:
        print("❌ No analysis-related cron jobs found")
        # Show all jobs for reference
        print("\nAll cron jobs:")
        for job in jobs:
            print(f"  • {job.get('title', 'N/A')} (ID: {job.get('jobId', 'N/A')}) - Status: {job.get('status', 'N/A')}")
    else:
        print(f"Found {len(analysis_jobs)} analysis-related cron jobs:")
        print()
        
        for job in analysis_jobs:
            job_id = job.get('jobId')
            title = job.get('title', 'N/A')
            status = job.get('status', 'N/A')
            enabled = job.get('enabled', False)
            url = job.get('url', 'N/A')
            schedule = job.get('schedule', {})
            timezone = schedule.get('timezone', 'N/A')
            
            print(f"📋 {title}")
            print(f"   ID: {job_id}")
            print(f"   Status: {status}")
            print(f"   Enabled: {'✅' if enabled else '❌'}")
            print(f"   URL: {url}")
            print(f"   Timezone: {timezone}")
            
            # Get recent execution history
            if job_id:
                try:
                    history_response = get_job_history(job_id)
                    executions = history_response.get('history', [])
                    
                    if executions:
                        print(f"   Recent executions:")
                        for i, execution in enumerate(executions[:3], 1):  # Show last 3
                            date = execution.get('date', 'N/A')
                            status = execution.get('status', 'N/A')
                            duration = execution.get('duration', 'N/A')
                            response_code = execution.get('httpStatus', 'N/A')
                            
                            print(f"     {i}. {date} | Status: {status} | HTTP: {response_code} | Duration: {duration}ms")
                    else:
                        print(f"   No execution history found")
                
                except Exception as e:
                    print(f"   ❌ Error getting history: {str(e)}")
            
            print()

except Exception as e:
    print(f"❌ Error checking cron jobs: {str(e)}")

print("=" * 50)