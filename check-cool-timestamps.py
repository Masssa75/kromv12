#!/usr/bin/env python3
"""Check COOL token timestamp issues"""
import requests
from datetime import datetime

# Get COOL token data
MANAGEMENT_TOKEN = "sbp_97ca99b1a82b9ed514d259a119ea3c19a2e42cd7"
PROJECT_REF = "eucfoommxxvqmmwdbkdv"

def run_query(query):
    response = requests.post(
        f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query",
        headers={"Authorization": f"Bearer {MANAGEMENT_TOKEN}", "Content-Type": "application/json"},
        json={"query": query}
    )
    return response.json()

# Get COOL tokens
cool_data = run_query("""
SELECT ticker, created_at, buy_timestamp, 
       raw_data->>'timestamp' as raw_timestamp,
       raw_data->'token'->>'pairTimestamp' as pair_timestamp,
       price_at_call, ath_price, ath_roi_percent
FROM crypto_calls 
WHERE ticker = 'COOL' 
ORDER BY created_at ASC 
LIMIT 5
""")

print("COOL Token Timestamp Analysis:")
print("-" * 80)

for token in cool_data:
    print(f"\nCreated at: {token['created_at']}")
    print(f"Buy timestamp: {token['buy_timestamp']}")
    print(f"Raw timestamp: {token['raw_timestamp']}")
    print(f"Pair timestamp: {token['pair_timestamp']}")
    
    if token['raw_timestamp']:
        ts = int(token['raw_timestamp'])
        print(f"  → Raw date: {datetime.fromtimestamp(ts)}")
    
    if token['pair_timestamp']:
        ts = int(token['pair_timestamp'])
        print(f"  → Pair date: {datetime.fromtimestamp(ts)}")
    
    print(f"Price at call: ${float(token['price_at_call'] or 0):.10f}")
    print(f"ATH price: ${float(token['ath_price'] or 0):.10f}")
    print(f"ATH ROI: {token['ath_roi_percent']}%")

print("\n" + "-" * 80)
print("ISSUE: The timestamps are in 2025, but the token was likely called much earlier.")
print("The chart shows trading history going back months/years.")
print("We need to use created_at timestamp instead of the raw_data timestamp.")