#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv
from datetime import datetime, timezone

# Load environment variables
load_dotenv('/Users/marcschwyn/Desktop/projects/KROMV12/.env')

# Get Supabase credentials
SUPABASE_ACCESS_TOKEN = os.getenv('SUPABASE_ACCESS_TOKEN')
PROJECT_ID = 'eucfoommxxvqmmwdbkdv'

if not SUPABASE_ACCESS_TOKEN:
    print("ERROR: Missing SUPABASE_ACCESS_TOKEN in .env file")
    exit(1)

print("=== Checking Cron Job Configuration via Management API ===\n")

# Query cron jobs
sql_query = """
SELECT 
    jobid,
    jobname,
    schedule,
    active,
    command,
    database,
    username
FROM cron.job
WHERE command LIKE '%crypto-ath%'
ORDER BY jobid;
"""

response = requests.post(
    f"https://api.supabase.com/v1/projects/{PROJECT_ID}/database/query",
    headers={
        "Authorization": f"Bearer {SUPABASE_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    },
    json={"query": sql_query}
)

if response.status_code == 200:
    jobs = response.json()
    if jobs:
        print("Found ATH cron jobs:")
        for job in jobs:
            print(f"\nJob ID: {job['jobid']}")
            print(f"Name: {job['jobname']}")
            print(f"Schedule: {job['schedule']}")
            print(f"Active: {job['active']}")
            print(f"Command: {job['command'][:100]}...")
    else:
        print("❌ No ATH cron jobs found!")
else:
    print(f"Error querying cron jobs: {response.status_code}")
    print(response.text)

# Check recent job runs
print("\n=== Recent Job Executions ===")

sql_query2 = """
SELECT 
    jobid,
    status,
    return_message,
    start_time,
    end_time
FROM cron.job_run_details
WHERE command LIKE '%crypto-ath%'
ORDER BY start_time DESC
LIMIT 10;
"""

response2 = requests.post(
    f"https://api.supabase.com/v1/projects/{PROJECT_ID}/database/query",
    headers={
        "Authorization": f"Bearer {SUPABASE_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    },
    json={"query": sql_query2}
)

if response2.status_code == 200:
    runs = response2.json()
    if runs:
        print("\nLast 10 execution attempts:")
        for run in runs:
            start = run.get('start_time', 'Unknown')
            status = run.get('status', 'Unknown')
            message = run.get('return_message', 'No message')
            
            # Calculate time ago
            if start != 'Unknown':
                try:
                    start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    time_ago = (datetime.now(timezone.utc) - start_dt).total_seconds() / 60
                    start = f"{time_ago:.0f} min ago"
                except:
                    pass
            
            print(f"\n- Started: {start}")
            print(f"  Status: {status}")
            if message and message != 'No message':
                print(f"  Message: {message[:100]}")
    else:
        print("No recent job executions found")
else:
    print(f"Error querying job runs: {response2.status_code}")

# Check if any cron jobs exist at all
print("\n=== All Cron Jobs ===")

sql_query3 = """
SELECT 
    jobid,
    jobname,
    schedule,
    active
FROM cron.job
ORDER BY jobid;
"""

response3 = requests.post(
    f"https://api.supabase.com/v1/projects/{PROJECT_ID}/database/query",
    headers={
        "Authorization": f"Bearer {SUPABASE_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    },
    json={"query": sql_query3}
)

if response3.status_code == 200:
    all_jobs = response3.json()
    if all_jobs:
        print(f"\nTotal cron jobs: {len(all_jobs)}")
        for job in all_jobs:
            print(f"- [{job['jobid']}] {job['jobname']} - Schedule: {job['schedule']} - Active: {job['active']}")
    else:
        print("❌ No cron jobs found at all!")
else:
    print(f"Error querying all jobs: {response3.status_code}")