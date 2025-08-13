#!/usr/bin/env python3
"""Test the ATH verifier on ORC CITY token specifically"""

import os
import json
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get credentials
service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase_url = os.getenv('SUPABASE_URL')

# Target ORC CITY token
target_id = "f49838c7-f156-43e5-aa16-2147940c4dde"

# First, set ORC CITY's ath_verified_at to a very old date so it gets processed first
print(f"Setting ORC CITY (id: {target_id}) to be processed first...")
response = requests.patch(
    f"{supabase_url}/rest/v1/crypto_calls?id=eq.{target_id}",
    headers={
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}",
        "Content-Type": "application/json"
    },
    json={"ath_verified_at": "2020-01-01T00:00:00Z"}
)

# Get ORC CITY's current values
print("\nORC CITY's current values:")
response = requests.get(
    f"{supabase_url}/rest/v1/crypto_calls?select=ticker,ath_price,price_at_call,ath_roi_percent&id=eq.{target_id}",
    headers={
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}"
    }
)
orc_before = response.json()[0]
print(f"  Ticker: {orc_before['ticker']}")
print(f"  ATH Price: ${orc_before['ath_price']:.9f}")
print(f"  Price at Call: ${orc_before['price_at_call']:.9f}")
print(f"  ATH ROI: {orc_before['ath_roi_percent']:.0f}%")

# Run the verifier on ORC CITY
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

# Get ORC CITY's updated values
print("\n\nORC CITY's values after verification:")
response = requests.get(
    f"{supabase_url}/rest/v1/crypto_calls?select=ticker,ath_price,price_at_call,ath_roi_percent&id=eq.{target_id}",
    headers={
        "apikey": service_key,
        "Authorization": f"Bearer {service_key}"
    }
)
orc_after = response.json()[0]
print(f"  Ticker: {orc_after['ticker']}")
print(f"  ATH Price: ${orc_after['ath_price']:.9f}")
print(f"  Price at Call: ${orc_after['price_at_call']:.9f}")
print(f"  ATH ROI: {orc_after['ath_roi_percent']:.0f}%")

# Check if value changed
if orc_before['ath_price'] != orc_after['ath_price']:
    print(f"\n⚠️ ATH CHANGED from ${orc_before['ath_price']:.9f} to ${orc_after['ath_price']:.9f}")
    change_percent = abs(orc_before['ath_price'] - orc_after['ath_price']) / orc_before['ath_price'] * 100
    print(f"   Change: {change_percent:.1f}%")
else:
    print(f"\n✅ ATH remained correct at ${orc_after['ath_price']:.9f}")