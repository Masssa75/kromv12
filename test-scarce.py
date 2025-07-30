#!/usr/bin/env python3
"""Test SCARCE token with fixed algorithm"""
import requests
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Token data from database
TOKEN_ID = "6fc92299-aec9-42ee-a3d3-236341a34116"
TICKER = "SCARCE"
NETWORK = "solana"
POOL = "3PgBfWRW3iv76oSZhHJhDUa4iE1aRgGPSmRUE5GSjP9b"
PRICE_AT_CALL = 0.0119108784
CREATED_AT = "2025-07-29 03:01:01.848268+00"

# Import and run the fixed processor
import sys
sys.path.append('.')
exec(open('fixed-parallel-ath.py').read().split('if __name__')[0])

# Create token data tuple
token_data = (TOKEN_ID, TICKER, NETWORK, POOL, None, str(PRICE_AT_CALL), {})

print(f"Testing SCARCE token with fixed ATH calculation")
print(f"Entry price: ${PRICE_AT_CALL}")
print(f"Created at: {CREATED_AT}")
print("-" * 60)

# Process it
result = process_single_token(token_data)

# Check result
if result == 1:
    # Query the updated data
    import requests
    response = requests.post(
        f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query",
        headers={"Authorization": f"Bearer {MANAGEMENT_TOKEN}", "Content-Type": "application/json"},
        json={"query": f"SELECT ath_price, ath_roi_percent, ath_timestamp FROM crypto_calls WHERE id = '{TOKEN_ID}'"}
    )
    data = response.json()
    if data:
        print(f"\n✅ Results:")
        print(f"ATH Price: ${float(data[0]['ath_price']):.8f}")
        print(f"ATH ROI: {data[0]['ath_roi_percent']}%")
        print(f"ATH Time: {data[0]['ath_timestamp']}")
else:
    print("\n❌ Processing failed!")