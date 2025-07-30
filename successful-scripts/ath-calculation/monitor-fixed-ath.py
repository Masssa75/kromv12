#!/usr/bin/env python3
"""Monitor fixed ATH processing progress"""
import requests
import time
from datetime import datetime

MANAGEMENT_TOKEN = "sbp_97ca99b1a82b9ed514d259a119ea3c19a2e42cd7"
PROJECT_REF = "eucfoommxxvqmmwdbkdv"

def get_count():
    """Get current ATH count"""
    response = requests.post(
        f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query",
        headers={"Authorization": f"Bearer {MANAGEMENT_TOKEN}", "Content-Type": "application/json"},
        json={"query": "SELECT COUNT(*) FROM crypto_calls WHERE ath_price IS NOT NULL;"}
    )
    return response.json()[0]['count']

def get_remaining():
    """Get remaining count"""
    response = requests.post(
        f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query",
        headers={"Authorization": f"Bearer {MANAGEMENT_TOKEN}", "Content-Type": "application/json"},
        json={"query": "SELECT COUNT(*) FROM crypto_calls WHERE pool_address IS NOT NULL AND price_at_call IS NOT NULL AND ath_price IS NULL;"}
    )
    return response.json()[0]['count']

print("Monitoring FIXED ATH processing...")
print("Press Ctrl+C to stop\n")

start_time = time.time()
start_count = get_count()
total = 5553

try:
    while True:
        current = get_count()
        remaining = get_remaining()
        elapsed = time.time() - start_time
        new_processed = current - start_count
        
        if new_processed > 0:
            rate = new_processed / (elapsed / 60)
            eta = remaining / rate if rate > 0 else 0
            
            print(f"\r[{datetime.now().strftime('%H:%M:%S')}] "
                  f"Processed: {current}/{total} ({current/total*100:.1f}%) | "
                  f"New: {new_processed} | "
                  f"Rate: {rate:.1f}/min | "
                  f"ETA: {int(eta)} min", end='', flush=True)
        else:
            print(f"\r[{datetime.now().strftime('%H:%M:%S')}] "
                  f"Waiting for processing to start... "
                  f"Current: {current}/{total}", end='', flush=True)
        
        if remaining == 0:
            print(f"\n\n✅ Processing complete! All {total} tokens processed.")
            break
        
        time.sleep(10)
        
except KeyboardInterrupt:
    print(f"\n\nStopped monitoring. Final count: {get_count()}/{total}")