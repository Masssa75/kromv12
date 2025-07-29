import json
import urllib.request
import urllib.error
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
KROM_API_TOKEN = env_vars['KROM_API_TOKEN']

def get_calls_needing_update(limit=100):
    """Get calls that need trade data (no trade section in raw_data)"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += "?select=krom_id,ticker,buy_timestamp,created_at,raw_data"
    # Get all calls to check for missing trade section in Python
    url += "&order=created_at.desc"
    url += f"&limit={limit}"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        all_calls = json.loads(response.read().decode())
        
        # Filter for calls that don't have trade section
        calls_needing_update = []
        for call in all_calls:
            raw_data = call.get('raw_data', {})
            if not raw_data or 'trade' not in raw_data:
                calls_needing_update.append(call)
        
        return calls_needing_update
    except Exception as e:
        print(f"Error fetching calls: {e}")
        return []

def fetch_krom_data_by_timestamp(timestamp, limit=100):
    """Fetch data from KROM API using beforeTimestamp parameter"""
    url = f"https://krom.one/api/v1/calls?beforeTimestamp={timestamp}&limit={limit}"
    
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {KROM_API_TOKEN}')
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        return data.get('data', [])
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        return []
    except Exception as e:
        print(f"Error fetching from KROM: {e}")
        return []

def find_call_in_krom_data(krom_id, krom_data):
    """Find a specific call by ID in KROM data"""
    for call in krom_data:
        if call.get('id') == krom_id:
            return call
    return None

def update_call_raw_data(krom_id, raw_data):
    """Update a call's raw_data in Supabase"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls?krom_id=eq.{krom_id}"
    
    update_data = {
        "raw_data": raw_data
    }
    
    data = json.dumps(update_data).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, method='PATCH')
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')
    req.add_header('Content-Type', 'application/json')
    req.add_header('Prefer', 'return=representation')
    
    try:
        response = urllib.request.urlopen(req)
        if response.status == 200:
            return True
        return False
    except Exception as e:
        print(f"Error updating {krom_id}: {e}")
        return False

def process_batch_smart(calls):
    """Process a batch of calls using smart timestamp-based fetching"""
    if not calls:
        return 0, 0
    
    updated = 0
    failed = 0
    
    # Group calls by similar timestamps (within 1 hour)
    timestamp_groups = {}
    for call in calls:
        timestamp = call.get('buy_timestamp')
        if timestamp:
            # Round to nearest hour
            hour_key = int(timestamp / 3600) * 3600
            if hour_key not in timestamp_groups:
                timestamp_groups[hour_key] = []
            timestamp_groups[hour_key].append(call)
    
    # Process each timestamp group
    for hour_timestamp, group_calls in timestamp_groups.items():
        # Fetch KROM data for this time period
        # Add 1 hour to ensure we get all calls in this group
        fetch_timestamp = hour_timestamp + 3600
        
        print(f"  Fetching KROM data before timestamp {fetch_timestamp}...")
        krom_data = fetch_krom_data_by_timestamp(fetch_timestamp, limit=100)
        
        if not krom_data:
            print(f"  ⚠️  No data returned from KROM API")
            failed += len(group_calls)
            continue
        
        # Process each call in this group
        for call in group_calls:
            krom_id = call['krom_id']
            ticker = call.get('ticker', 'Unknown')
            
            # Find this call in KROM data
            krom_call = find_call_in_krom_data(krom_id, krom_data)
            
            if krom_call:
                # Update with complete raw_data
                if update_call_raw_data(krom_id, krom_call):
                    updated += 1
                    if 'trade' in krom_call:
                        buy_price = krom_call['trade'].get('buyPrice', 'N/A')
                        print(f"    ✅ Updated {ticker} with trade data (buyPrice: {buy_price})")
                    else:
                        print(f"    ✅ Updated {ticker} (no trade executed)")
                else:
                    failed += 1
                    print(f"    ❌ Failed to update {ticker}")
            else:
                # If not found, we might need to paginate further
                failed += 1
                print(f"    ⚠️  {ticker} not found in KROM batch")
        
        # Rate limit - KROM API might have limits
        time.sleep(0.5)
    
    return updated, failed

print("=== Repopulate All Raw Data from KROM API ===")
print(f"Started at: {datetime.now()}\n")

# Count total calls needing update
print("Counting calls that need raw_data update...")
test_batch = get_calls_needing_update(limit=1)
if test_batch:
    # Get rough count by checking a larger batch
    large_batch = get_calls_needing_update(limit=10000)
    total_needing_update = len(large_batch)
    print(f"Approximately {total_needing_update:,} calls need raw_data update\n")
else:
    print("No calls need updating!")
    exit()

# Process in batches
batch_size = 50
total_updated = 0
total_failed = 0
batch_num = 0

print(f"Processing in batches of {batch_size}...\n")

while True:
    batch_num += 1
    
    # Get next batch
    calls = get_calls_needing_update(limit=batch_size)
    
    if not calls:
        print("\nNo more calls to process!")
        break
    
    print(f"Batch {batch_num}: Processing {len(calls)} calls...")
    
    # Show sample from this batch
    sample_tickers = [f"{c.get('ticker', 'Unknown')}" for c in calls[:3]]
    print(f"  Samples: {', '.join(sample_tickers)}...")
    
    # Process this batch
    updated, failed = process_batch_smart(calls)
    
    total_updated += updated
    total_failed += failed
    
    print(f"  Batch result: {updated} updated, {failed} failed")
    
    # Progress report every 5 batches
    if batch_num % 5 == 0:
        print(f"\n--- Progress Report ---")
        print(f"Total updated: {total_updated:,}")
        print(f"Total failed: {total_failed:,}")
        print(f"Success rate: {total_updated/(total_updated+total_failed)*100:.1f}%")
        print("---\n")
    
    # Stop after 10 batches for testing
    if batch_num >= 10:
        print("\nStopping after 10 batches (testing mode)")
        print("Remove this limit to process all calls")
        break

print(f"\n{'='*60}")
print(f"=== FINAL SUMMARY ===")
print(f"Total calls processed: {total_updated + total_failed:,}")
print(f"Successfully updated: {total_updated:,}")
print(f"Failed: {total_failed:,}")
if total_updated + total_failed > 0:
    print(f"Success rate: {total_updated/(total_updated+total_failed)*100:.1f}%")
else:
    print("No calls were processed")
print(f"{'='*60}")

# Verify results
print("\nVerifying results...")
remaining = get_calls_needing_update(limit=10)
if remaining:
    print(f"Still {len(remaining)} calls showing in sample (may be recently failed ones)")
else:
    print("✅ All calls appear to have raw_data!")

print(f"\nFinished at: {datetime.now()}")