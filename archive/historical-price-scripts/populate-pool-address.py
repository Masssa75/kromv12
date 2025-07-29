import json
import urllib.request
import time
from datetime import datetime

# Load environment variables
env_vars = {}
with open('.env', 'r') as f:
    for line in f:
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.strip().split('=', 1)
            env_vars[k] = v.strip()

SUPABASE_URL = env_vars['SUPABASE_URL']
SUPABASE_SERVICE_ROLE_KEY = env_vars['SUPABASE_SERVICE_ROLE_KEY']

def count_calls_with_pool_in_raw_data():
    """Count how many calls have pool address in raw_data"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += "?select=krom_id"
    url += "&raw_data->token->pa=not.is.null"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    req.add_header('Range', '0-10000')
    req.add_header('Prefer', 'count=exact')
    
    try:
        response = urllib.request.urlopen(req)
        content_range = response.headers.get('content-range')
        if content_range:
            total = int(content_range.split('/')[-1])
            return total
        return 0
    except Exception as e:
        print(f"Error counting: {e}")
        return 0

def get_calls_with_pool_data(limit=100, offset=0):
    """Get calls that have pool address in raw_data but not in pool_address column"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += "?select=krom_id,ticker,raw_data,pool_address"
    url += "&raw_data->token->pa=not.is.null"
    url += "&pool_address=is.null"  # Only get ones not yet populated
    url += f"&limit={limit}"
    url += f"&offset={offset}"
    url += "&order=created_at.desc"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching: {e}")
        return []

def update_pool_address(krom_id, pool_address):
    """Update pool_address for a specific call"""
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
        return response.status == 200
    except Exception as e:
        print(f"Error updating {krom_id}: {e}")
        return False

print("=== Populate pool_address Column from raw_data ===")
print(f"Started at: {datetime.now()}\n")

# First, count how many need updating
total_with_pool = count_calls_with_pool_in_raw_data()
print(f"Total calls with pool address in raw_data: {total_with_pool:,}")

# Get initial batch to check
test_batch = get_calls_with_pool_data(limit=5)
if test_batch:
    print(f"\nSample of calls to update:")
    for call in test_batch:
        pool_from_raw = call.get('raw_data', {}).get('token', {}).get('pa')
        print(f"- {call.get('ticker')}: {pool_from_raw[:30]}...")

# Process in batches
batch_size = 50
total_updated = 0
total_failed = 0
batch_num = 0

print(f"\nProcessing in batches of {batch_size}...")

while True:
    batch_num += 1
    
    # Get next batch
    calls = get_calls_with_pool_data(limit=batch_size, offset=0)  # Always offset 0 since we're updating
    
    if not calls:
        print("\nNo more calls to process!")
        break
    
    print(f"\nBatch {batch_num}: Processing {len(calls)} calls...")
    
    batch_updated = 0
    batch_failed = 0
    
    for call in calls:
        krom_id = call['krom_id']
        ticker = call.get('ticker', 'Unknown')
        pool_address = call.get('raw_data', {}).get('token', {}).get('pa')
        
        if pool_address:
            if update_pool_address(krom_id, pool_address):
                batch_updated += 1
                total_updated += 1
                if batch_updated <= 3:  # Show first few
                    print(f"  ✅ {ticker}: {pool_address[:30]}...")
            else:
                batch_failed += 1
                total_failed += 1
                if batch_failed <= 3:
                    print(f"  ❌ Failed to update {ticker}")
        else:
            print(f"  ⚠️  {ticker} has no pool address in raw_data")
    
    print(f"  Batch result: {batch_updated} updated, {batch_failed} failed")
    
    # Progress report every 10 batches
    if batch_num % 10 == 0:
        print(f"\n--- Progress: {total_updated:,} updated so far ---")
    
    # Safety limit for testing
    if batch_num >= 100:  # Process up to 5,000 records
        print("\nReached batch limit for this run")
        break
    
    # Small delay to avoid overwhelming the API
    time.sleep(0.2)

print(f"\n{'='*60}")
print(f"=== FINAL SUMMARY ===")
print(f"Total calls updated: {total_updated:,}")
print(f"Total failed: {total_failed:,}")
if total_updated + total_failed > 0:
    print(f"Success rate: {total_updated/(total_updated+total_failed)*100:.1f}%")
print(f"{'='*60}")

# Verify results
print("\nVerifying population...")
test_verify = get_calls_with_pool_data(limit=1)
if test_verify:
    print(f"Still {len(test_verify)} calls need pool_address population")
else:
    print("✅ All calls with pool data have been populated!")

print(f"\nFinished at: {datetime.now()}")