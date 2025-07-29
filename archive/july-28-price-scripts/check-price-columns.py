#!/usr/bin/env python3
import json
import urllib.request

print("=== Checking Price Column Status ===")
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

# Check a sample record to see what columns exist
query_url = f"{supabase_url}?select=krom_id,ticker,historical_price_usd,price_at_call,price_source&limit=10&historical_price_usd=not.is.null"
req = urllib.request.Request(query_url)
req.add_header('apikey', service_key)
req.add_header('Authorization', f'Bearer {service_key}')

try:
    response = urllib.request.urlopen(req)
    results = json.loads(response.read().decode())
    
    print(f"Sample records with historical_price_usd:")
    for i, record in enumerate(results[:5]):
        print(f"{i+1}. {record['ticker']}:")
        print(f"   historical_price_usd: ${record.get('historical_price_usd', 'None')}")
        print(f"   price_at_call: ${record.get('price_at_call', 'None')}")
        print(f"   price_source: {record.get('price_source', 'None')}")
        print()
        
except Exception as e:
    print(f"Error: {e}")

# Check counts
print("\n📊 Column Statistics:")

# Count records with historical_price_usd
hist_url = f"{supabase_url}?select=count&historical_price_usd=not.is.null"
req = urllib.request.Request(hist_url)
req.add_header('apikey', service_key)
req.add_header('Authorization', f'Bearer {service_key}')
req.add_header('Prefer', 'count=exact')

try:
    response = urllib.request.urlopen(req)
    hist_count = int(response.headers.get('content-range', '0-0/0').split('/')[-1])
    print(f"Records with historical_price_usd: {hist_count}")
except:
    print("Could not get historical_price_usd count")

# Count records with price_at_call
price_url = f"{supabase_url}?select=count&price_at_call=not.is.null"
req = urllib.request.Request(price_url)
req.add_header('apikey', service_key)
req.add_header('Authorization', f'Bearer {service_key}')
req.add_header('Prefer', 'count=exact')

try:
    response = urllib.request.urlopen(req)
    price_count = int(response.headers.get('content-range', '0-0/0').split('/')[-1])
    print(f"Records with price_at_call: {price_count}")
except:
    print("Could not get price_at_call count")

print("\n💡 Recommendation:")
print("If price_at_call column exists but is mostly empty, we should:")
print("1. Copy data from historical_price_usd to price_at_call")
print("2. Update crypto-poller to populate price_at_call going forward")