#!/usr/bin/env python3
"""
Test the updated crypto-ultra-tracker to verify market cap updates
"""

import os
import json
import time
import warnings
warnings.filterwarnings("ignore")
import requests
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Initialize Supabase
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

print("=" * 60)
print("Testing crypto-ultra-tracker Market Cap Updates")
print("=" * 60)

# Get a sample token with supply data
initial_result = supabase.table('crypto_calls').select(
    'id,ticker,current_price,current_market_cap,ath_price,ath_market_cap,circulating_supply,total_supply'
).not_.is_('total_supply', 'null').not_.is_('current_price', 'null').limit(5).execute()

if not initial_result.data:
    print("No tokens with supply data found")
    exit(1)

print("\nBefore ultra-tracker update:")
for token in initial_result.data[:3]:
    print(f"\n{token['ticker']}:")
    print(f"  Current price: ${token['current_price']:.8f}")
    print(f"  Current MC: ${token['current_market_cap']:,.0f}" if token['current_market_cap'] else "  Current MC: None")
    print(f"  Circulating supply: {token['circulating_supply']:,.0f}" if token['circulating_supply'] else "  Circulating supply: None")
    expected_mc = float(token['current_price']) * float(token['circulating_supply']) if token['circulating_supply'] else 0
    if expected_mc > 0:
        print(f"  Expected MC: ${expected_mc:,.0f}")

# Trigger ultra-tracker with small batch for testing
print("\n" + "-" * 60)
print("Triggering crypto-ultra-tracker (test batch)...")

url = f"{os.getenv('SUPABASE_URL')}/functions/v1/crypto-ultra-tracker"
headers = {
    'Authorization': f"Bearer {os.getenv('SUPABASE_SERVICE_ROLE_KEY')}",
    'Content-Type': 'application/json'
}
payload = {
    'batchSize': 5,    # Small batch for testing
    'delayMs': 50,
    'maxTokens': 20    # Process only first 20 tokens
}

response = requests.post(url, headers=headers, json=payload)

if response.status_code == 200:
    result = response.json()
    print(f"✅ Ultra-tracker completed successfully!")
    print(f"   Processed: {result.get('totalProcessed', 0)} tokens")
    print(f"   Updated: {result.get('totalUpdated', 0)} tokens")
    print(f"   New ATHs: {result.get('newATHs', 0)}")
    print(f"   Time: {result.get('processingTimeMs', 0)}ms")
else:
    print(f"❌ Error: {response.status_code}")
    print(response.text[:500])

# Wait a moment for database to update
time.sleep(2)

# Check if market caps were updated
print("\n" + "-" * 60)
print("After ultra-tracker update:")

# Re-fetch the same tokens
token_ids = [t['id'] for t in initial_result.data[:3]]
for token_id in token_ids:
    result = supabase.table('crypto_calls').select(
        'ticker,current_price,current_market_cap,ath_price,ath_market_cap,circulating_supply,total_supply'
    ).eq('id', token_id).execute()
    
    if result.data:
        token = result.data[0]
        print(f"\n{token['ticker']}:")
        print(f"  Current price: ${token['current_price']:.8f}")
        print(f"  Current MC: ${token['current_market_cap']:,.0f}" if token['current_market_cap'] else "  Current MC: None")
        
        # Verify market cap calculation
        if token['circulating_supply'] and token['current_price']:
            expected_mc = float(token['current_price']) * float(token['circulating_supply'])
            actual_mc = float(token['current_market_cap']) if token['current_market_cap'] else 0
            
            if actual_mc > 0:
                diff_percent = abs(actual_mc - expected_mc) / expected_mc * 100 if expected_mc > 0 else 0
                if diff_percent < 1:
                    print(f"  ✅ Market cap correctly calculated")
                else:
                    print(f"  ⚠️ Market cap mismatch: {diff_percent:.1f}% difference")

print("\n" + "=" * 60)
print("Test Complete!")
print("=" * 60)