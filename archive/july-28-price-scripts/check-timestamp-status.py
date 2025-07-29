#!/usr/bin/env python3
import json
import urllib.request

print("=== Checking Timestamp Status ===")
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

# Check tokens without buy_timestamp
no_timestamp_url = f"{supabase_url}?buy_timestamp=is.null&select=count"
req = urllib.request.Request(no_timestamp_url)
req.add_header('apikey', service_key)
req.add_header('Authorization', f'Bearer {service_key}')
req.add_header('Prefer', 'count=exact')

try:
    response = urllib.request.urlopen(req)
    no_timestamp_count = int(response.headers.get('content-range', '0-0/0').split('/')[-1])
    print(f"Tokens without buy_timestamp: {no_timestamp_count}")
except:
    print(f"Could not get count")

# Check tokens with KROM price available
query_url = f"{supabase_url}?select=krom_id,ticker,raw_data&raw_data->>trade.buyPrice=not.is.null&limit=5"
req = urllib.request.Request(query_url)
req.add_header('apikey', service_key)
req.add_header('Authorization', f'Bearer {service_key}')

try:
    response = urllib.request.urlopen(req)
    tokens = json.loads(response.read().decode())
    
    print(f"\nSample tokens with KROM price:")
    for token in tokens:
        price = token['raw_data'].get('trade', {}).get('buyPrice', 0)
        print(f"  {token['ticker']}: ${price}")
except:
    print("Could not get samples")

# Check current price source distribution
dist_url = f"{supabase_url}?select=price_source&limit=1000&order=price_updated_at.desc"
req = urllib.request.Request(dist_url)
req.add_header('apikey', service_key)
req.add_header('Authorization', f'Bearer {service_key}')

try:
    response = urllib.request.urlopen(req)
    results = json.loads(response.read().decode())
    
    # Count by source
    source_counts = {}
    for result in results:
        source = result.get('price_source', 'null/empty') or 'null/empty'
        source_counts[source] = source_counts.get(source, 0) + 1
    
    print(f"\nRecent price source updates (last 1000):")
    for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {source}: {count}")
except Exception as e:
    print(f"Could not get distribution: {e}")