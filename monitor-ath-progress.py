#!/usr/bin/env python3
"""Monitor ATH processing progress"""
import requests
import time
from datetime import datetime

MANAGEMENT_TOKEN = "sbp_97ca99b1a82b9ed514d259a119ea3c19a2e42cd7"
PROJECT_REF = "eucfoommxxvqmmwdbkdv"

def get_count():
    response = requests.post(
        f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query",
        headers={"Authorization": f"Bearer {MANAGEMENT_TOKEN}", "Content-Type": "application/json"},
        json={"query": "SELECT COUNT(*) FROM crypto_calls WHERE ath_price IS NOT NULL"}
    )
    return response.json()[0]['count']

def get_total():
    response = requests.post(
        f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query",
        headers={"Authorization": f"Bearer {MANAGEMENT_TOKEN}", "Content-Type": "application/json"},
        json={"query": "SELECT COUNT(*) FROM crypto_calls WHERE pool_address IS NOT NULL AND price_at_call IS NOT NULL"}
    )
    return response.json()[0]['count']

print("Monitoring ATH processing progress...")
print("Press Ctrl+C to stop\n")

start_count = get_count()
total = get_total()
start_time = time.time()

while True:
    current = get_count()
    elapsed = time.time() - start_time
    processed = current - start_count
    
    if processed > 0:
        rate = processed / (elapsed / 60)  # per minute
        remaining = total - current
        eta = remaining / rate if rate > 0 else 0
        
        print(f"\r[{datetime.now().strftime('%H:%M:%S')}] "
              f"Processed: {current}/{total} ({current/total*100:.1f}%) | "
              f"New: {processed} | "
              f"Rate: {rate:.1f}/min | "
              f"ETA: {eta:.0f} min", end='', flush=True)
    else:
        print(f"\r[{datetime.now().strftime('%H:%M:%S')}] "
              f"Current: {current}/{total} ({current/total*100:.1f}%) | "
              f"Waiting for processing to start...", end='', flush=True)
    
    time.sleep(10)  # Check every 10 seconds