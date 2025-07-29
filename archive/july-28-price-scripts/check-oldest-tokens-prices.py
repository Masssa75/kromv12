#\!/usr/bin/env python3
import json
import urllib.request
from datetime import datetime

print("=== Checking Oldest Tokens for Price Data ===")
print()

# Get service key
service_key = None
try:
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('SUPABASE_SERVICE_ROLE_KEY='):
                service_key = line.split('=', 1)[1].strip()
                break
except:
    print("❌ Could not read .env file")
    exit(1)

supabase_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/rest/v1/crypto_calls"

# Check specific tokens from the screenshot
tokens = ['PEPEV2', 'T0R', 'CODON', 'VITALIKSAMA', 'ANNABELLE', 'CC', 'SPEECHLY', 'FINESHYT', 'MEME', 'BIP177']

print(f"Checking {len(tokens)} tokens from the screenshot...")
print()

for ticker in tokens:
    query_url = f"{supabase_url}?select=krom_id,ticker,created_at,buy_timestamp,price_at_call,historical_price_usd,price_source,raw_data&ticker=eq.{ticker}&limit=1"
    
    req = urllib.request.Request(query_url)
    req.add_header('apikey', service_key)
    req.add_header('Authorization', f'Bearer {service_key}')
    
    try:
        response = urllib.request.urlopen(req)
        records = json.loads(response.read().decode())
        
        if records:
            record = records[0]
            print(f"Token: {ticker}")
            print(f"  Created: {record.get('created_at', 'N/A')}")
            print(f"  Buy timestamp: {record.get('buy_timestamp', 'N/A')}")
            print(f"  Price at call: {record.get('price_at_call', 'N/A')}")
            print(f"  Historical price: {record.get('historical_price_usd', 'N/A')}")
            print(f"  Price source: {record.get('price_source', 'N/A')}")
            
            # Check if raw_data has trade info
            raw_data = record.get('raw_data', {})
            if raw_data and 'trade' in raw_data:
                print(f"  KROM buyPrice: {raw_data['trade'].get('buyPrice', 'N/A')}")
            else:
                print(f"  KROM buyPrice: No trade data")
            print()
        else:
            print(f"Token {ticker} not found")
            print()
            
    except Exception as e:
        print(f"Error checking {ticker}: {e}")
        print()

# Also check the very oldest tokens in the database
print("\n=== Checking Very Oldest Tokens ===")
query_url = f"{supabase_url}?select=krom_id,ticker,created_at,buy_timestamp,price_at_call,historical_price_usd,price_source&order=created_at.asc&limit=20"

req = urllib.request.Request(query_url)
req.add_header('apikey', service_key)
req.add_header('Authorization', f'Bearer {service_key}')

try:
    response = urllib.request.urlopen(req)
    records = json.loads(response.read().decode())
    
    print(f"\nFound {len(records)} oldest records:")
    for i, record in enumerate(records):
        has_price = record.get('price_at_call') is not None
        print(f"{i+1}. {record['ticker']} - Created: {record['created_at'][:10]} - Has price: {has_price}")
        
except Exception as e:
    print(f"Error: {e}")

