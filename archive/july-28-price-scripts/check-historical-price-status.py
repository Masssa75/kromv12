#!/usr/bin/env python3
import json
import urllib.request

print("=== Checking Historical Price Status ===")
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
    print(f"Total tokens in database: {total_count}")
except:
    total_count = "Unknown"
    print(f"Total tokens in database: Unknown")

# Get count without historical prices
no_price_url = f"{supabase_url}?historical_price_usd=is.null&select=count"
req = urllib.request.Request(no_price_url)
req.add_header('apikey', service_key)
req.add_header('Authorization', f'Bearer {service_key}')
req.add_header('Prefer', 'count=exact')

try:
    response = urllib.request.urlopen(req)
    no_price_count = int(response.headers.get('content-range', '0-0/0').split('/')[-1])
    print(f"Tokens without historical price: {no_price_count}")
except:
    no_price_count = "Unknown"
    print(f"Tokens without historical price: Unknown")

# Get distribution by price_source
dist_url = f"{supabase_url}?select=price_source&limit=10000"
req = urllib.request.Request(dist_url)
req.add_header('apikey', service_key)
req.add_header('Authorization', f'Bearer {service_key}')

try:
    response = urllib.request.urlopen(req)
    results = json.loads(response.read().decode())
    
    # Count by source
    source_counts = {}
    for result in results:
        source = result.get('price_source', 'null/empty')
        source_counts[source] = source_counts.get(source, 0) + 1
    
    print(f"\nPrice source distribution:")
    for source, count in sorted(source_counts.items()):
        pct = (count / len(results) * 100) if len(results) > 0 else 0
        print(f"  {source}: {count} ({pct:.1f}%)")
        
except Exception as e:
    print(f"Could not get distribution: {e}")

# Show batch processing estimates
if isinstance(no_price_count, int) and no_price_count > 0:
    batch_size = 50
    num_batches = (no_price_count + batch_size - 1) // batch_size
    
    # Estimate time (0.5s per token + overhead)
    est_time_seconds = no_price_count * 0.5 + (num_batches * 5)
    est_time_minutes = est_time_seconds / 60
    
    print(f"\n📊 Batch Processing Estimates:")
    print(f"  Tokens to process: {no_price_count}")
    print(f"  Batch size: {batch_size}")
    print(f"  Number of batches: {num_batches}")
    print(f"  Estimated time: ~{est_time_minutes:.1f} minutes")
    print(f"\n💡 Ready to start batch processing!")