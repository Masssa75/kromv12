#\!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
}

# Get actual BIP177 records
query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=ticker,krom_id,current_price&ticker.eq.BIP177&limit=10"
response = requests.get(query, headers=headers)

if response.status_code == 200:
    bip177_records = response.json()
    print(f"🔍 BIP177 records found: {len(bip177_records)}")
    for i, record in enumerate(bip177_records):
        price = record.get('current_price')
        if price and price > 0:
            print(f"   {i+1}. KROM ID: {record['krom_id']}, Current Price: ${price:.8f} ✅")
        else:
            print(f"   {i+1}. KROM ID: {record['krom_id']}, Current Price: None ❌")

# Count tokens with actual prices
query2 = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=ticker,current_price,roi_percent&current_price.gt.0&order=price_updated_at.desc&limit=30"
response2 = requests.get(query2, headers=headers)

if response2.status_code == 200:
    tokens = response2.json()
    print(f"\n✅ Tokens successfully updated with current prices:")
    seen_tickers = set()
    unique_count = 0
    
    for token in tokens:
        ticker = token['ticker']
        if ticker not in seen_tickers:
            seen_tickers.add(ticker)
            unique_count += 1
            roi = token.get('roi_percent')
            roi_str = f" (ROI: {roi:+.1f}%)" if roi is not None else ""
            print(f"   {unique_count}. {ticker}: ${token['current_price']:.8f}{roi_str}")
    
    print(f"\n📊 Summary: {unique_count} unique tokens have current prices")

# Check total count with proper header
import urllib.parse

count_query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id&current_price.gt.0"
count_headers = {**headers, "Prefer": "count=exact"}
response3 = requests.head(count_query, headers=count_headers)

if response3.status_code == 200:
    content_range = response3.headers.get('content-range', '')
    if '/' in content_range:
        total = content_range.split('/')[-1]
        print(f"\n📈 TOTAL tokens with current prices: {total}")
