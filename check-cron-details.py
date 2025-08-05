#!/usr/bin/env python3
import os
import requests
import json
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

print("=== ATH Cron Job Configuration ===\n")

# Query for the ATH cron job
sql_query = """
SELECT 
    jobid,
    jobname,
    schedule,
    active,
    command
FROM cron.job
WHERE jobname = 'ath-continuous-update';
"""

response = requests.post(
    f"https://api.supabase.com/v1/projects/{PROJECT_ID}/database/query",
    headers={
        "Authorization": f"Bearer {SUPABASE_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    },
    json={"query": sql_query}
)

if response.status_code in [200, 201]:
    jobs = response.json()
    if jobs and len(jobs) > 0:
        job = jobs[0]
        print("✅ ATH Cron Job Found:")
        print(f"- Job ID: {job['jobid']}")
        print(f"- Name: {job['jobname']}")
        print(f"- Schedule: {job['schedule']} (runs every minute)")
        print(f"- Active: {'YES' if job['active'] else 'NO'}")
        print(f"- Command: Calls crypto-ath-update with limit=25")
    else:
        print("❌ No ATH cron job found!")

# Check recent job runs
print("\n=== Recent Job Execution History ===")

sql_query2 = """
SELECT 
    runid,
    status,
    return_message,
    start_time,
    end_time
FROM cron.job_run_details
WHERE jobid = 3
ORDER BY start_time DESC
LIMIT 20;
"""

response2 = requests.post(
    f"https://api.supabase.com/v1/projects/{PROJECT_ID}/database/query",
    headers={
        "Authorization": f"Bearer {SUPABASE_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    },
    json={"query": sql_query2}
)

if response2.status_code in [200, 201]:
    runs = response2.json()
    if runs:
        # Group by status
        success_count = sum(1 for r in runs if r.get('status') == 'succeeded')
        failed_count = sum(1 for r in runs if r.get('status') == 'failed')
        
        print(f"\nLast 20 runs: {success_count} succeeded, {failed_count} failed")
        
        # Show last few runs
        print("\nRecent executions:")
        for run in runs[:5]:
            start = run.get('start_time', 'Unknown')
            status = run.get('status', 'Unknown')
            message = run.get('return_message', '')
            
            # Calculate time ago
            if start != 'Unknown':
                try:
                    start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
                    time_ago = (datetime.now(timezone.utc) - start_dt).total_seconds() / 60
                    start_str = f"{time_ago:.0f} min ago"
                except:
                    start_str = start
            
            status_icon = "✅" if status == "succeeded" else "❌"
            print(f"\n{status_icon} {start_str} - Status: {status}")
            if message and status == "failed":
                print(f"   Error: {message[:100]}")
    else:
        print("No recent job executions found")

# Check if pg_net extension is enabled
print("\n=== Checking pg_net Extension ===")

sql_query3 = """
SELECT 
    extname,
    extversion
FROM pg_extension
WHERE extname IN ('pg_cron', 'pg_net');
"""

response3 = requests.post(
    f"https://api.supabase.com/v1/projects/{PROJECT_ID}/database/query",
    headers={
        "Authorization": f"Bearer {SUPABASE_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    },
    json={"query": sql_query3}
)

if response3.status_code in [200, 201]:
    extensions = response3.json()
    for ext in extensions:
        print(f"- {ext['extname']} v{ext['extversion']} ✅")

# Try to manually execute the cron job command
print("\n=== Testing Manual Execution ===")
print("Testing the edge function directly...")

test_response = requests.post(
    "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-ath-update",
    headers={
        "Content-Type": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Ria2R2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDc1NjI4ODEsImV4cCI6MjA2MzEzODg4MX0.eaWAToMH3go56vYwvYWpbkgibVTEiv72AtUrqiIChTs"
    },
    json={"limit": 5}
)

if test_response.status_code == 200:
    result = test_response.json()
    print(f"✅ Edge function working! Processed {result.get('processed', 0)} tokens")
else:
    print(f"❌ Edge function error: {test_response.status_code}")
    print(test_response.text)