#!/usr/bin/env python3
import json
import urllib.request
import time

print("=== Copying historical_price_usd to price_at_call (Batch Update) ===")
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

# Process in batches
BATCH_SIZE = 100
offset = 0
total_updated = 0

while True:
    # Get records that have historical_price_usd but not price_at_call
    query_url = f"{supabase_url}?select=krom_id,historical_price_usd&historical_price_usd=not.is.null&price_at_call=is.null&limit={BATCH_SIZE}&offset={offset}"
    
    req = urllib.request.Request(query_url)
    req.add_header('apikey', service_key)
    req.add_header('Authorization', f'Bearer {service_key}')
    
    try:
        response = urllib.request.urlopen(req)
        records = json.loads(response.read().decode())
        
        if not records:
            print(f"\n✅ No more records to update!")
            break
            
        print(f"\nProcessing batch {offset//BATCH_SIZE + 1} ({len(records)} records)...")
        
        # Update each record
        batch_updated = 0
        for record in records:
            krom_id = record['krom_id']
            historical_price = record['historical_price_usd']
            
            # Update this record
            update_url = f"{supabase_url}?krom_id=eq.{krom_id}"
            update_data = json.dumps({'price_at_call': historical_price})
            
            update_req = urllib.request.Request(
                update_url,
                data=update_data.encode('utf-8'),
                headers={
                    'apikey': service_key,
                    'Authorization': f'Bearer {service_key}',
                    'Content-Type': 'application/json',
                    'Prefer': 'return=minimal'
                },
                method='PATCH'
            )
            
            try:
                urllib.request.urlopen(update_req)
                batch_updated += 1
                print(f".", end="", flush=True)
            except Exception as e:
                print(f"\n❌ Error updating {krom_id}: {e}")
            
            # Small delay to avoid rate limits
            time.sleep(0.01)
        
        print(f" ✅ Updated {batch_updated} records")
        total_updated += batch_updated
        offset += BATCH_SIZE
        
    except Exception as e:
        print(f"\n❌ Error fetching batch: {e}")
        break

print(f"\n{'='*60}")
print(f"SUMMARY")
print(f"{'='*60}")
print(f"Total records updated: {total_updated}")

# Verify the results
print("\nVerifying results...")

# Check count of price_at_call
count_url = f"{supabase_url}?select=count&price_at_call=not.is.null"
req = urllib.request.Request(count_url)
req.add_header('apikey', service_key)
req.add_header('Authorization', f'Bearer {service_key}')
req.add_header('Prefer', 'count=exact')

try:
    response = urllib.request.urlopen(req)
    count = int(response.headers.get('content-range', '0-0/0').split('/')[-1])
    print(f"✅ Records with price_at_call: {count}")
except:
    print("Could not verify count")

print("\n🎉 The entry prices should now appear in the krom-analysis-app!")