#!/usr/bin/env python3
import os
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(supabase_url, supabase_key)

print("Checking cron jobs...\n")

try:
    # Try to query cron jobs using RPC
    result = supabase.rpc('get_cron_jobs').execute()
    print("Cron jobs found:", result.data)
except Exception as e:
    print(f"Could not query cron jobs directly: {e}")
    print("\nTrying alternative method...")
    
    # Check if any edge function invocations happened recently
    print("\nChecking recent edge function invocations...")
    
    # Test the ultra tracker directly
    import requests
    
    url = "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-ultra-tracker"
    headers = {
        "Authorization": f"Bearer {supabase_key}",
        "Content-Type": "application/json"
    }
    
    print("\nCalling crypto-ultra-tracker edge function directly...")
    try:
        response = requests.post(url, headers=headers, json={})
        print(f"Response status: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {response.text[:500]}")
        else:
            print(f"Error response: {response.text}")
    except Exception as e:
        print(f"Error calling edge function: {e}")