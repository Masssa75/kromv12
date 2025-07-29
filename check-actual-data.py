#!/usr/bin/env python3
"""
Check actual current price data
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json"
}

# Get actual records to see the data
print("📊 Fetching actual records to check current_price values...")

# Get 20 random records
query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=ticker,current_price,price_at_call,price_updated_at&limit=20&order=created_at.desc"
response = requests.get(query, headers=headers)

if response.status_code == 200:
    records = response.json()
    
    null_count = 0
    zero_count = 0
    positive_count = 0
    
    print("\nSample of 20 recent records:")
    for i, record in enumerate(records, 1):
        ticker = record['ticker']
        current = record['current_price']
        at_call = record['price_at_call']
        updated = record['price_updated_at']
        
        if current is None:
            null_count += 1
            status = "NULL"
        elif current == 0:
            zero_count += 1
            status = "ZERO"
        else:
            positive_count += 1
            status = f"${current:.8f}"
        
        print(f"{i:2d}. {ticker:10s} - Current: {status:20s} | At call: {at_call} | Updated: {updated}")
    
    print(f"\nCounts from this sample:")
    print(f"  NULL: {null_count}")
    print(f"  ZERO: {zero_count}")
    print(f"  >0: {positive_count}")

# Try a different approach - get tokens that need prices
print("\n\n📊 Looking for tokens that need current prices...")
query2 = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=ticker,contract_address,network,price_at_call,current_price&price_at_call.gt.0&or=(current_price.is.null,current_price.eq.0)&limit=10"
response2 = requests.get(query2, headers=headers)

if response2.status_code == 200:
    needs_price = response2.json()
    print(f"Found {len(needs_price)} tokens needing prices:")
    for token in needs_price[:5]:
        print(f"  - {token['ticker']} ({token['network']}) - price_at_call: {token['price_at_call']}")