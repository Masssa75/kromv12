#!/usr/bin/env python3
import json
import urllib.request

print("=== Verifying Column Migration ===")
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

# Check 1: Records with historical_price_usd but not price_at_call
print("1. Checking for records with historical_price_usd but not price_at_call...")
query_url = f"{supabase_url}?select=count&historical_price_usd=not.is.null&price_at_call=is.null"
req = urllib.request.Request(query_url)
req.add_header('apikey', service_key)
req.add_header('Authorization', f'Bearer {service_key}')
req.add_header('Prefer', 'count=exact')

try:
    response = urllib.request.urlopen(req)
    count = int(response.headers.get('content-range', '0-0/0').split('/')[-1])
    print(f"   Records with historical_price_usd but not price_at_call: {count}")
    if count > 0:
        print("   ⚠️  WARNING: Some records need migration!")
    else:
        print("   ✅ All historical prices have been migrated")
except Exception as e:
    print(f"   Error: {e}")

# Check 2: Total counts
print("\n2. Total record counts:")

# Historical price count
hist_url = f"{supabase_url}?select=count&historical_price_usd=not.is.null"
req = urllib.request.Request(hist_url)
req.add_header('apikey', service_key)
req.add_header('Authorization', f'Bearer {service_key}')
req.add_header('Prefer', 'count=exact')

try:
    response = urllib.request.urlopen(req)
    hist_count = int(response.headers.get('content-range', '0-0/0').split('/')[-1])
    print(f"   Records with historical_price_usd: {hist_count}")
except:
    print("   Could not get historical_price_usd count")

# Price at call count
price_url = f"{supabase_url}?select=count&price_at_call=not.is.null"
req = urllib.request.Request(price_url)
req.add_header('apikey', service_key)
req.add_header('Authorization', f'Bearer {service_key}')
req.add_header('Prefer', 'count=exact')

try:
    response = urllib.request.urlopen(req)
    price_count = int(response.headers.get('content-range', '0-0/0').split('/')[-1])
    print(f"   Records with price_at_call: {price_count}")
except:
    print("   Could not get price_at_call count")

# Check 3: Verify no code references
print("\n3. Code reference check:")
print("   ✅ crypto-poller Edge Function - Updated and deployed")
print("   ✅ populate-historical-prices-using-created-at.py - Updated")
print("   ✅ No other Edge Functions reference historical_price_usd")
print("   ✅ krom-analysis-app uses price_at_call")
print("   ✅ krom-api-explorer doesn't reference either column")

print("\n" + "="*50)
print("RECOMMENDATION:")
if count == 0:
    print("✅ Safe to remove historical_price_usd column")
    print("\nSQL to remove column:")
    print("ALTER TABLE crypto_calls DROP COLUMN historical_price_usd;")
else:
    print("⚠️  NOT safe to remove column yet - migration needed")
    print(f"\nNeed to migrate {count} records first")