#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

headers = {
    'apikey': SUPABASE_SERVICE_ROLE_KEY,
    'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
    'Content-Type': 'application/json'
}

# Query for tokens with prices
url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
params = {
    'select': 'ticker,price_at_call,current_price,ath_price,roi_percent,price_fetched_at,buy_timestamp,created_at',
    'order': 'created_at.desc',
    'limit': '20',
    'or': '(ticker.eq.BOB,ticker.eq.DP,ticker.eq.AI,ticker.eq.KAVR)',
    'price_at_call': 'not.is.null'
}

response = requests.get(url, headers=headers, params=params)
data = response.json()

print(f"Found {len(data)} tokens with prices\n")

for token in data:
    print(f"Token: {token['ticker']}")
    print(f"  Price at call: ${token.get('price_at_call', 'N/A')}")
    print(f"  Current price: ${token.get('current_price', 'N/A')}")
    print(f"  ATH price: ${token.get('ath_price', 'N/A')}")
    print(f"  ROI: {token.get('roi_percent', 'N/A')}%")
    print(f"  Call time: {token.get('buy_timestamp') or token.get('created_at')}")
    print(f"  Price fetched: {token.get('price_fetched_at', 'N/A')}")
    print()