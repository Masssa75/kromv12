#!/usr/bin/env python3
"""Simple ATH processor with better error handling"""
import requests
import time
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Configuration
MANAGEMENT_TOKEN = "sbp_97ca99b1a82b9ed514d259a119ea3c19a2e42cd7"
PROJECT_REF = "eucfoommxxvqmmwdbkdv"
GECKO_API_KEY = os.getenv("GECKO_TERMINAL_API_KEY", "")

print(f"Starting simple ATH processor...")
print(f"API Key: {GECKO_API_KEY[:10]}...")

# Test database connection
print("\nTesting database connection...")
try:
    response = requests.post(
        f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query",
        headers={"Authorization": f"Bearer {MANAGEMENT_TOKEN}", "Content-Type": "application/json"},
        json={"query": "SELECT COUNT(*) FROM crypto_calls WHERE ath_price IS NOT NULL"},
        timeout=10
    )
    count = response.json()[0]['count']
    print(f"✅ Database connected. Current ATH count: {count}")
except Exception as e:
    print(f"❌ Database error: {e}")
    exit(1)

# Get one token to process
print("\nFetching a token to process...")
try:
    response = requests.post(
        f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query",
        headers={"Authorization": f"Bearer {MANAGEMENT_TOKEN}", "Content-Type": "application/json"},
        json={"query": """
            SELECT id, ticker, network, pool_address, buy_timestamp, price_at_call, raw_data
            FROM crypto_calls
            WHERE pool_address IS NOT NULL 
            AND price_at_call IS NOT NULL
            AND ath_price IS NULL
            ORDER BY created_at ASC
            LIMIT 1
        """},
        timeout=10
    )
    tokens = response.json()
    if not tokens:
        print("No tokens to process!")
        exit(0)
    
    token = tokens[0]
    print(f"✅ Got token: {token['ticker']} on {token['network']}")
except Exception as e:
    print(f"❌ Error fetching token: {e}")
    exit(1)

# Process the token
print(f"\nProcessing {token['ticker']}...")
network_map = {'ethereum': 'eth', 'solana': 'solana', 'bsc': 'bsc'}
network = network_map.get(token['network'], token['network'])

# Test API call
api_url = f"https://pro-api.coingecko.com/api/v3/onchain/networks/{network}/pools/{token['pool_address']}/ohlcv/day"
print(f"API URL: {api_url}")

try:
    response = requests.get(
        api_url,
        params={'aggregate': 1, 'limit': 10},
        headers={'x-cg-pro-api-key': GECKO_API_KEY},
        timeout=30
    )
    print(f"API Response: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"✅ API call successful. Got {len(data.get('data', {}).get('attributes', {}).get('ohlcv_list', []))} candles")
    else:
        print(f"❌ API error: {response.text}")
except Exception as e:
    print(f"❌ API exception: {e}")

print("\nDone!")