import json
import urllib.request
import urllib.error
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
KROM_API_TOKEN = env_vars['KROM_API_TOKEN']

def fetch_krom_batch(before_timestamp=None, limit=100):
    """Fetch a batch from KROM API"""
    url = f"https://krom.one/api/v1/calls?limit={limit}"
    if before_timestamp:
        url += f"&beforeTimestamp={before_timestamp}"
    
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {KROM_API_TOKEN}')
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"\nError: {e}")
        return []

def update_batch_in_supabase(krom_calls):
    """Update multiple calls efficiently"""
    updated = 0
    with_trade = 0
    
    for call in krom_calls:
        krom_id = call.get('id')
        if not krom_id:
            continue
            
        url = f"{SUPABASE_URL}/rest/v1/crypto_calls?krom_id=eq.{krom_id}"
        data = json.dumps({"raw_data": call}).encode('utf-8')
        
        req = urllib.request.Request(url, data=data, method='PATCH')
        req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
        req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')
        req.add_header('Content-Type', 'application/json')
        
        try:
            response = urllib.request.urlopen(req)
            if response.status == 200:
                updated += 1
                if 'trade' in call:
                    with_trade += 1
        except:
            pass
    
    return updated, with_trade

print("=== Batch Processor for Raw Data Repopulation ===")
print(f"Started at: {datetime.now()}")
print("Press Ctrl+C to stop at any time\n")

# Configuration
BATCH_SIZE = 100
MAX_BATCHES = 20  # Process 20 batches at a time
DELAY_BETWEEN_BATCHES = 0.5

# Initialize
total_updated = 0
total_with_trade = 0
last_timestamp = None
batch_num = 0

try:
    for run in range(MAX_BATCHES):
        batch_num += 1
        
        # Fetch batch
        sys.stdout.write(f"\rBatch {batch_num}: Fetching... ")
        sys.stdout.flush()
        
        calls = fetch_krom_batch(before_timestamp=last_timestamp, limit=BATCH_SIZE)
        
        if not calls:
            print("\nNo more data available")
            break
        
        # Update progress
        sys.stdout.write(f"\rBatch {batch_num}: Processing {len(calls)} calls... ")
        sys.stdout.flush()
        
        # Update in Supabase
        updated, with_trade = update_batch_in_supabase(calls)
        total_updated += updated
        total_with_trade += with_trade
        
        # Get oldest timestamp for next batch
        timestamps = [c.get('timestamp', float('inf')) for c in calls]
        last_timestamp = min(timestamps) if timestamps else None
        
        # Show results
        trade_pct = (with_trade/updated*100) if updated > 0 else 0
        sys.stdout.write(f"\rBatch {batch_num}: ✓ {updated} updated ({with_trade} with trade, {trade_pct:.0f}%)")
        
        if last_timestamp:
            date_str = datetime.fromtimestamp(last_timestamp).strftime('%Y-%m-%d')
            sys.stdout.write(f" - Oldest: {date_str}")
        
        print()  # New line
        
        # Delay between batches
        time.sleep(DELAY_BETWEEN_BATCHES)
        
except KeyboardInterrupt:
    print("\n\nStopped by user")

# Summary
print(f"\n{'='*60}")
print(f"Total calls updated: {total_updated:,}")
print(f"Calls with trade data: {total_with_trade:,}")
if total_updated > 0:
    print(f"Trade data percentage: {total_with_trade/total_updated*100:.1f}%")
print(f"{'='*60}")

# Quick database check
print("\nChecking current database status...")
url = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=raw_data&limit=5000"
req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)

try:
    response = urllib.request.urlopen(req)
    calls = json.loads(response.read().decode())
    with_trade = sum(1 for c in calls if c.get('raw_data', {}).get('trade'))
    print(f"Database now has {with_trade:,} calls with trade data")
except:
    pass

print(f"\nFinished at: {datetime.now()}")