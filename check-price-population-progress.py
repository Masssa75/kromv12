#!/usr/bin/env python3
import json
import urllib.request

print("=== Checking Price Population Progress ===")
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

# Get total count
total_url = f"{supabase_url}?select=count"
req = urllib.request.Request(total_url)
req.add_header('apikey', service_key)
req.add_header('Authorization', f'Bearer {service_key}')
req.add_header('Prefer', 'count=exact')

try:
    response = urllib.request.urlopen(req)
    total_count = int(response.headers.get('content-range', '0-0/0').split('/')[-1])
except:
    total_count = 0

# Get counts by price_source
sources = ['KROM', 'GECKO_CREATED_AT', 'GECKO_BUY_TIMESTAMP', 'GECKO_LIVE', 'DEAD_TOKEN', 'NO_POOL', 'NO_TIMESTAMP']
source_counts = {}

for source in sources:
    url = f"{supabase_url}?price_source=eq.{source}&select=count"
    req = urllib.request.Request(url)
    req.add_header('apikey', service_key)
    req.add_header('Authorization', f'Bearer {service_key}')
    req.add_header('Prefer', 'count=exact')
    
    try:
        response = urllib.request.urlopen(req)
        count = int(response.headers.get('content-range', '0-0/0').split('/')[-1])
        source_counts[source] = count
    except:
        source_counts[source] = 0

# Count without historical price
no_price_url = f"{supabase_url}?historical_price_usd=is.null&select=count"
req = urllib.request.Request(no_price_url)
req.add_header('apikey', service_key)
req.add_header('Authorization', f'Bearer {service_key}')
req.add_header('Prefer', 'count=exact')

try:
    response = urllib.request.urlopen(req)
    no_price_count = int(response.headers.get('content-range', '0-0/0').split('/')[-1])
except:
    no_price_count = 0

# Count with historical price
with_price_count = total_count - no_price_count

print(f"📊 DATABASE STATUS:")
print(f"Total tokens: {total_count}")
print(f"With historical price: {with_price_count} ({with_price_count/total_count*100:.1f}%)")
print(f"Without historical price: {no_price_count} ({no_price_count/total_count*100:.1f}%)")
print()

print(f"📈 PRICE SOURCE BREAKDOWN:")
total_sourced = 0
for source, count in source_counts.items():
    if count > 0:
        total_sourced += count
        pct = (count / total_count * 100) if total_count > 0 else 0
        print(f"  {source}: {count} ({pct:.1f}%)")

print()
print(f"💡 INSIGHTS:")

# Calculate success rate
successful_sources = ['KROM', 'GECKO_CREATED_AT', 'GECKO_BUY_TIMESTAMP', 'GECKO_LIVE']
success_count = sum(source_counts.get(s, 0) for s in successful_sources)
failed_sources = ['DEAD_TOKEN', 'NO_POOL', 'NO_TIMESTAMP']
failed_count = sum(source_counts.get(s, 0) for s in failed_sources)

if success_count + failed_count > 0:
    success_rate = (success_count / (success_count + failed_count) * 100)
    print(f"  Success rate: {success_rate:.1f}% ({success_count} successful / {success_count + failed_count} attempted)")
    print(f"  KROM prices: {source_counts.get('KROM', 0)}")
    print(f"  GeckoTerminal prices: {success_count - source_counts.get('KROM', 0)}")
    print(f"  Failed/Dead: {failed_count}")

print(f"\n🚀 REMAINING WORK:")
print(f"  Tokens still need prices: {no_price_count}")
if no_price_count > 0:
    batches_remaining = (no_price_count + 49) // 50
    est_time = batches_remaining * 2  # ~2 minutes per batch
    print(f"  Estimated batches: {batches_remaining}")
    print(f"  Estimated time: ~{est_time} minutes")