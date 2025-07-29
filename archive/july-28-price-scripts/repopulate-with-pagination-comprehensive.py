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

def fetch_krom_api_with_timestamp(before_timestamp=None, limit=100):
    """Fetch calls from KROM API with optional beforeTimestamp"""
    url = f"https://krom.one/api/v1/calls?limit={limit}"
    if before_timestamp:
        url += f"&beforeTimestamp={before_timestamp}"
    
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {KROM_API_TOKEN}')
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        if isinstance(data, list):
            return data
        return data.get('data', [])
    except Exception as e:
        print(f"Error fetching from KROM: {e}")
        return []

def update_call_in_supabase(krom_call):
    """Update a single call with complete raw_data"""
    krom_id = krom_call.get('id')
    if not krom_id:
        return False
    
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls?krom_id=eq.{krom_id}"
    
    update_data = {
        "raw_data": krom_call
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

def count_calls_without_trade():
    """Count how many calls don't have trade data"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += "?select=krom_id"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    req.add_header('Range', '0-10000')
    req.add_header('Prefer', 'count=exact')
    
    try:
        response = urllib.request.urlopen(req)
        content_range = response.headers.get('content-range')
        if content_range:
            total = int(content_range.split('/')[-1])
            # We know ~2.2% have trade data, so ~97.8% don't
            return int(total * 0.978)
        return 0
    except Exception as e:
        print(f"Error counting: {e}")
        return 0

print("=== Comprehensive Raw Data Repopulation with Pagination ===")
print(f"Started at: {datetime.now()}\n")

# Count how many need updating
total_without_trade = count_calls_without_trade()
print(f"Estimated calls without trade data: {total_without_trade:,}\n")

# Process in batches with pagination
total_updated = 0
total_with_trade = 0
batch_num = 0
last_timestamp = None
consecutive_empty = 0
max_batches = 50  # Limit for this run

print(f"Processing up to {max_batches} batches of 100 calls each...\n")

while batch_num < max_batches:
    batch_num += 1
    
    # Fetch batch from KROM API
    print(f"Batch {batch_num}: ", end="")
    krom_calls = fetch_krom_api_with_timestamp(before_timestamp=last_timestamp, limit=100)
    
    if not krom_calls:
        consecutive_empty += 1
        print("No data returned")
        if consecutive_empty >= 3:
            print("\nNo more data available from KROM API")
            break
        time.sleep(2)  # Wait before retry
        continue
    
    consecutive_empty = 0
    calls_with_trade = sum(1 for c in krom_calls if 'trade' in c)
    print(f"Fetched {len(krom_calls)} calls ({calls_with_trade} with trade)")
    
    # Update each call
    batch_updated = 0
    batch_with_trade = 0
    
    for krom_call in krom_calls:
        if update_call_in_supabase(krom_call):
            batch_updated += 1
            if 'trade' in krom_call:
                batch_with_trade += 1
    
    total_updated += batch_updated
    total_with_trade += batch_with_trade
    
    print(f"  → Updated {batch_updated} calls ({batch_with_trade} with trade)")
    
    # Get the oldest timestamp for next batch
    if krom_calls:
        # Find the minimum timestamp
        timestamps = [c.get('timestamp', float('inf')) for c in krom_calls]
        last_timestamp = min(timestamps)
        oldest_date = datetime.fromtimestamp(last_timestamp).strftime('%Y-%m-%d %H:%M')
        print(f"  → Oldest call in batch: {oldest_date}")
    
    # Progress report every 10 batches
    if batch_num % 10 == 0:
        print(f"\n--- Progress Report ---")
        print(f"Total calls updated: {total_updated:,}")
        print(f"Calls with trade data: {total_with_trade:,} ({total_with_trade/total_updated*100:.1f}%)")
        print(f"Estimated remaining: ~{total_without_trade - total_updated:,}")
        print("---\n")
    
    # Rate limiting
    time.sleep(0.5)

print(f"\n{'='*60}")
print(f"=== FINAL SUMMARY ===")
print(f"Batches processed: {batch_num}")
print(f"Total calls updated: {total_updated:,}")
print(f"Calls with trade data: {total_with_trade:,} ({total_with_trade/total_updated*100:.1f}% have trade)")
print(f"Estimated remaining without trade: ~{total_without_trade - total_with_trade:,}")
print(f"{'='*60}")

print(f"\nTo continue processing, run this script again.")
print(f"It will automatically paginate to older calls.")

print(f"\nFinished at: {datetime.now()}")