#!/usr/bin/env python3
"""Find TRADE token details"""
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
        result = response.json()
        print(f"Query result: {result}")
        return result
    except Exception as e:
        print(f"Query error: {e}")
        return []

# Search for TRADE tokens
print("Searching for TRADE tokens...")
search_query = """
SELECT id, ticker, contract_address, network, pool_address, 
       buy_timestamp, price_at_call, ath_price, ath_roi_percent,
       created_at
FROM crypto_calls
WHERE ticker = 'TRADE'
ORDER BY created_at DESC
LIMIT 10
"""

results = run_query(search_query)
if results:
    print(f"\nFound {len(results)} TRADE tokens:")
    for i, token in enumerate(results):
        print(f"\n{i+1}. {token['ticker']} on {token['network']}")
        print(f"   Contract: {token['contract_address']}")
        print(f"   Pool: {token['pool_address']}")
        print(f"   Buy time: {token['buy_timestamp']}")
        print(f"   Entry price: ${token['price_at_call']}")
        print(f"   ATH price: ${token['ath_price']}")
        print(f"   ATH ROI: {token['ath_roi_percent']}%")
else:
    print("No TRADE tokens found!")

# Also check the specific contract from the screenshot
print("\n\nChecking specific contract from screenshot...")
specific_query = """
SELECT id, ticker, contract_address, network, pool_address,
       buy_timestamp, price_at_call, ath_price, ath_roi_percent
FROM crypto_calls  
WHERE pool_address = '0x95Ea82bAaA0B7b5cE4D8A7f46fb289049e6d3154'
   OR pool_address = '0x3FEb6c3fa7758A8DF653946104a6ac3CE6a7828a'
LIMIT 5
"""

specific_results = run_query(specific_query)