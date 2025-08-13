#!/usr/bin/env python3
"""Test the ATH verifier on T1 token specifically"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials
service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase_url = os.getenv('SUPABASE_URL')

# Target the specific T1 token we're testing
target_id = "d4bb24ed-1348-45c1-a744-6a5722b7feaf"

# First, set T1's ath_verified_at to a very old date so it gets processed first
print(f"Setting T1 (id: {target_id}) to be processed first...")
response = requests.patch(
    f"{supabase_url}/rest/v1/crypto_calls?id=eq.{target_id}",
    headers={
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json"
    },
    json={"ath_verified_at": "2020-01-01T00:00:00Z"}
)

# Get T1's current values
print("\nT1's current values:")
response = requests.get(
    f"{supabase_url}/rest/v1/crypto_calls?select=ticker,ath_price,price_at_call,ath_roi_percent&id=eq.{target_id}",
    headers={
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}"
    }
)
t1_before = response.json()[0]
print(f"  Ticker: {t1_before['ticker']}")
print(f"  ATH Price: ${t1_before['ath_price']:.9f}")
print(f"  Price at Call: ${t1_before['price_at_call']:.9f}")
print(f"  ATH ROI: {t1_before['ath_roi_percent']:.0f}%")

# Run the verifier on T1
print("\nRunning ATH verifier...")
response = requests.post(
    f"{supabase_url}/functions/v1/crypto-ath-verifier",
    headers={
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json"
    },
    json={"limit": 1}
)

result = response.json()
print(f"\nVerifier response:")
print(f"  Processed: {result.get('processed', 0)}")
print(f"  Discrepancies Found: {result.get('discrepanciesFound', 0)}")

if result.get('results'):
    for token_result in result['results']:
        print(f"\n  Token: {token_result['ticker']}")
        print(f"  Calculated ATH: ${token_result['ath_price']:.9f}")
        print(f"  Stored ATH: ${token_result.get('storedATH', 0):.9f}")
        print(f"  Has Discrepancy: {token_result['hasDiscrepancy']}")
        if token_result['hasDiscrepancy']:
            print(f"  Discrepancy Type: {token_result['discrepancyType']}")

# Get T1's updated values
print("\n\nT1's values after verification:")
response = requests.get(
    f"{supabase_url}/rest/v1/crypto_calls?select=ticker,ath_price,price_at_call,ath_roi_percent&id=eq.{target_id}",
    headers={
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}"
    }
)
t1_after = response.json()[0]
print(f"  Ticker: {t1_after['ticker']}")
print(f"  ATH Price: ${t1_after['ath_price']:.9f}")
print(f"  Price at Call: ${t1_after['price_at_call']:.9f}")
print(f"  ATH ROI: {t1_after['ath_roi_percent']:.0f}%")

# Check if value changed
if t1_before['ath_price'] != t1_after['ath_price']:
    print(f"\n⚠️ ATH CHANGED from ${t1_before['ath_price']:.9f} to ${t1_after['ath_price']:.9f}")
else:
    print(f"\n✅ ATH remained correct at ${t1_after['ath_price']:.9f}")