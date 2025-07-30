#!/usr/bin/env python3
"""
Simple ATH processor using management API
"""
import requests
import time
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# API configuration
MANAGEMENT_TOKEN = "sbp_97ca99b1a82b9ed514d259a119ea3c19a2e42cd7"
PROJECT_REF = "eucfoommxxvqmmwdbkdv"
API_KEY = os.getenv("GECKO_TERMINAL_API_KEY", "")

def run_query(query):
    """Run a query via Supabase Management API"""
    response = requests.post(
        f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query",
        headers={"Authorization": f"Bearer {MANAGEMENT_TOKEN}", "Content-Type": "application/json"},
        json={"query": query}
    )
    return response.json()

print("Checking current ATH count...")
result = run_query("SELECT COUNT(*) FROM crypto_calls WHERE ath_price IS NOT NULL")
print(f"Current ATH count: {result[0]['count']}")

print("\nStarting batch processing via edge function...")

# Try to invoke the edge function with a simpler method
import subprocess

# Run the edge function via supabase CLI
cmd = f"""SUPABASE_ACCESS_TOKEN={MANAGEMENT_TOKEN} npx supabase functions invoke crypto-ath-historical --data '{{"limit": 50}}'"""

print("Running edge function...")
result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
print("Output:", result.stdout)
print("Error:", result.stderr)

# Check new count
time.sleep(5)
result = run_query("SELECT COUNT(*) FROM crypto_calls WHERE ath_price IS NOT NULL")
print(f"\nNew ATH count: {result[0]['count']}")