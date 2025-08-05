#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/Users/marcschwyn/Desktop/projects/KROMV12/.env')

# Get Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("ERROR: Missing Supabase credentials in .env file")
    exit(1)

print("=== Checking Cron Jobs ===\n")

# Try to query cron.job table directly via SQL
sql_query = """
SELECT jobid, jobname, schedule, active, command 
FROM cron.job 
ORDER BY jobid;
"""

response = requests.post(
    f"{SUPABASE_URL}/rest/v1/rpc/query",
    headers={
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json"
    },
    json={"query": sql_query}
)

if response.status_code == 200:
    print("Cron jobs found:")
    results = response.json()
    for job in results:
        print(f"- Job {job['jobid']}: {job['jobname']}")
        print(f"  Schedule: {job['schedule']}")
        print(f"  Active: {job['active']}")
        print(f"  Command: {job['command'][:100]}...")
else:
    print(f"Error checking cron jobs: {response.status_code}")
    print(response.text)

# Alternative: Check recent function invocations
print("\n=== Recent Edge Function Invocations ===")
print("To check via dashboard:")
print("1. Go to https://supabase.com/dashboard")
print("2. Select your project")
print("3. Go to Edge Functions > crypto-ath-update")
print("4. Check the Logs tab for recent executions")