#!/usr/bin/env python3
"""Recalculate ATH for TRADE token"""
import requests

# Configuration
MANAGEMENT_TOKEN = "sbp_97ca99b1a82b9ed514d259a119ea3c19a2e42cd7"
PROJECT_REF = "eucfoommxxvqmmwdbkdv"

def run_query(query):
    """Execute query"""
    try:
        response = requests.post(
            f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query",
            headers={"Authorization": f"Bearer {MANAGEMENT_TOKEN}", "Content-Type": "application/json"},
            json={"query": query},
            timeout=10
        )
        return response.json()
    except Exception as e:
        print(f"Query error: {e}")
        return []

# Clear the ATH for TRADE token so it can be recalculated
print("Clearing ATH data for TRADE token...")
clear_query = """
UPDATE crypto_calls
SET ath_price = NULL,
    ath_timestamp = NULL,
    ath_roi_percent = NULL
WHERE id = '9a7efa22-d73d-4e12-b67d-d9e8a075740a'
"""

result = run_query(clear_query)
print(f"Clear result: {result}")

# Verify it was cleared
verify_query = """
SELECT ticker, ath_price, ath_roi_percent
FROM crypto_calls
WHERE id = '9a7efa22-d73d-4e12-b67d-d9e8a075740a'
"""

verify_result = run_query(verify_query)
print(f"\nVerification - ATH should be NULL:")
print(verify_result)

print("\nNow the TRADE token can be reprocessed by the ATH calculation script.")
print("However, since it's on 'hyperevm' network which may not be supported by GeckoTerminal,")
print("the ATH calculation might fail again.")
print("\nThe current ATH of $8.50 from entry of $0.00147 = 577,743% ROI")
print("This seems extremely high and might be due to:")
print("1. Wrong pool data")
print("2. Price spike from a low liquidity pool")
print("3. Data error in the original calculation")