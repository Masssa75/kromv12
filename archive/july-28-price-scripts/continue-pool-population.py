import json
import urllib.request
import time
from datetime import datetime
import sys

# Load environment variables
env_vars = {}
with open('.env', 'r') as f:
    for line in f:
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.strip().split('=', 1)
            env_vars[k] = v.strip()

SUPABASE_URL = env_vars['SUPABASE_URL']
SUPABASE_SERVICE_ROLE_KEY = env_vars['SUPABASE_SERVICE_ROLE_KEY']

def get_calls_needing_pool(limit=200):
    """Get calls that need pool address populated"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += "?select=krom_id,ticker,raw_data"
    url += "&raw_data->token->pa=not.is.null"
    url += "&pool_address=is.null"
    url += f"&limit={limit}"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching: {e}")
        return []

def update_pool_batch(updates):
    """Update multiple pool addresses efficiently"""
    success_count = 0
    
    for krom_id, pool_address in updates:
        url = f"{SUPABASE_URL}/rest/v1/crypto_calls?krom_id=eq.{krom_id}"
        
        data = json.dumps({
            "pool_address": pool_address
        }).encode('utf-8')
        
        req = urllib.request.Request(url, data=data, method='PATCH')
        req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
        req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')
        req.add_header('Content-Type', 'application/json')
        
        try:
            response = urllib.request.urlopen(req)
            if response.status == 200 or response.status == 204:
                success_count += 1
        except Exception as e:
            pass
    
    return success_count

print("=== Continue Pool Address Population ===")
print(f"Started at: {datetime.now()}\n")

total_updated = 0
batch_num = 0
batch_size = 100

print("Processing remaining records...")

while True:
    # Get next batch
    calls = get_calls_needing_pool(limit=batch_size)
    
    if not calls:
        print("\n✅ All records processed!")
        break
    
    batch_num += 1
    sys.stdout.write(f"\rBatch {batch_num}: Processing {len(calls)} records... ")
    sys.stdout.flush()
    
    # Prepare updates
    updates = []
    for call in calls:
        krom_id = call['krom_id']
        pool = call.get('raw_data', {}).get('token', {}).get('pa')
        if pool:
            updates.append((krom_id, pool))
    
    # Update batch
    if updates:
        success = update_pool_batch(updates)
        total_updated += success
        sys.stdout.write(f"Updated {success}/{len(updates)}")
        sys.stdout.flush()
    
    # Show progress every 10 batches
    if batch_num % 10 == 0:
        print(f"\n--- Total updated so far: {total_updated:,} ---")
    
    # Small delay
    time.sleep(0.1)
    
    # Safety limit
    if batch_num >= 200:  # 20,000 records max
        print("\n\nReached batch limit")
        break

print(f"\n\n{'='*60}")
print(f"Total records updated: {total_updated:,}")
print(f"{'='*60}")

# Final check
url = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=krom_id&pool_address=not.is.null"
req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
req.add_header('Range', '0-10000')
req.add_header('Prefer', 'count=exact')

try:
    response = urllib.request.urlopen(req)
    content_range = response.headers.get('content-range')
    if content_range:
        total = int(content_range.split('/')[-1])
        print(f"\nTotal records with pool_address: {total:,}")
except:
    pass

print(f"\nFinished at: {datetime.now()}")