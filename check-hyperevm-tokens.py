#!/usr/bin/env python3
"""Check hyperevm token statistics"""
import requests

MANAGEMENT_TOKEN = "sbp_97ca99b1a82b9ed514d259a119ea3c19a2e42cd7"
PROJECT_REF = "eucfoommxxvqmmwdbkdv"

def run_query(query):
    response = requests.post(
        f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query",
        headers={"Authorization": f"Bearer {MANAGEMENT_TOKEN}", "Content-Type": "application/json"},
        json={"query": query}
    )
    return response.json()

# Get total count
total = run_query("SELECT COUNT(*) as count FROM crypto_calls WHERE network = 'hyperevm'")
print(f"Total hyperevm tokens: {total[0]['count']}")

# With ATH data
with_ath = run_query("SELECT COUNT(*) as count FROM crypto_calls WHERE network = 'hyperevm' AND ath_price IS NOT NULL")
print(f"Hyperevm tokens with ATH data: {with_ath[0]['count']}")

# Show examples
examples = run_query("""
    SELECT ticker, price_at_call, ath_price, ath_roi_percent, created_at
    FROM crypto_calls
    WHERE network = 'hyperevm' AND ath_price IS NOT NULL
    ORDER BY ath_roi_percent DESC
    LIMIT 10
""")

print("\nTop 10 hyperevm tokens by ATH ROI:")
for token in examples:
    roi = float(token['ath_roi_percent']) if token['ath_roi_percent'] else 0.0
    entry = float(token['price_at_call']) if token['price_at_call'] else 0.0
    ath = float(token['ath_price']) if token['ath_price'] else 0.0
    print(f"{token['ticker']}: Entry ${entry:.8f} → ATH ${ath:.8f} = {roi:,.1f}%")

# Check if all have unrealistic ROIs
high_roi = run_query("""
    SELECT COUNT(*) as count 
    FROM crypto_calls 
    WHERE network = 'hyperevm' 
    AND ath_price IS NOT NULL 
    AND ath_roi_percent > 10000
""")
print(f"\nHyperevm tokens with >10,000% ROI: {high_roi[0]['count']}")

# Check pool addresses
print("\nChecking pool address patterns...")
pools = run_query("""
    SELECT DISTINCT pool_address
    FROM crypto_calls
    WHERE network = 'hyperevm'
    LIMIT 5
""")
print(f"Sample pool addresses:")
for pool in pools:
    print(f"  {pool['pool_address']}")