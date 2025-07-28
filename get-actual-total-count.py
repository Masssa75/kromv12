import json
import urllib.request
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

print("=== Getting Actual Database Counts ===")
print(f"Date: {datetime.now()}")

# Method 1: Use count=exact with Prefer header
print("\n1. Using count=exact method...")
url = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=count&count=exact"
req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
req.add_header('Prefer', 'count=exact')

try:
    response = urllib.request.urlopen(req)
    
    # Check Content-Range header for total count
    content_range = response.headers.get('Content-Range', '')
    print(f"   Content-Range header: {content_range}")
    
    if '*/' in content_range:
        total_count = int(content_range.split('*/')[-1])
        print(f"   Total calls: {total_count:,}")
    else:
        data = json.loads(response.read().decode())
        print(f"   Response data: {data}")
        
except Exception as e:
    print(f"   Error: {e}")

# Method 2: Get all records in batches to count
print("\n2. Counting with batch method...")
total_counted = 0
offset = 0
batch_size = 1000

while True:
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=krom_id&limit={batch_size}&offset={offset}"
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        
        batch_count = len(data)
        total_counted += batch_count
        
        print(f"   Batch {offset//batch_size + 1}: {batch_count} records (total so far: {total_counted:,})")
        
        if batch_count < batch_size:
            break  # Last batch
            
        offset += batch_size
        
        # Safety break to avoid infinite loop
        if total_counted > 10000:
            print("   Stopping at 10,000 records for safety")
            break
            
    except Exception as e:
        print(f"   Error in batch {offset//batch_size + 1}: {e}")
        break

print(f"\nTotal records counted: {total_counted:,}")

# Now check pool_address status on actual data
print(f"\n3. Checking pool_address status...")

# Check calls with pool_address populated
with_pool_count = 0
without_pool_count = 0
with_trade_data = 0

# Sample across different ranges to get better estimate
sample_ranges = [
    (0, 100),      # First 100
    (1000, 1100),  # Middle batch
    (2000, 2100),  # Another middle batch
    (max(0, total_counted - 100), total_counted)  # Last 100
]

total_sampled = 0

for start, end in sample_ranges:
    if start >= total_counted:
        continue
        
    actual_end = min(end, total_counted)
    limit = actual_end - start
    
    if limit <= 0:
        continue
    
    print(f"\n   Sampling records {start} to {actual_end}...")
    
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=krom_id,pool_address,raw_data&offset={start}&limit={limit}"
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        
        batch_with_pool = 0
        batch_without_pool = 0
        batch_with_trade = 0
        
        for call in data:
            if call.get('pool_address'):
                batch_with_pool += 1
            else:
                batch_without_pool += 1
                
            # Check for trade data
            raw_data = call.get('raw_data', {})
            trade = raw_data.get('trade', {})
            if trade.get('buyPrice') is not None:
                batch_with_trade += 1
        
        print(f"     With pool_address: {batch_with_pool}/{len(data)} ({batch_with_pool/len(data)*100:.1f}%)")
        print(f"     Without pool_address: {batch_without_pool}/{len(data)} ({batch_without_pool/len(data)*100:.1f}%)")
        print(f"     With trade data: {batch_with_trade}/{len(data)} ({batch_with_trade/len(data)*100:.1f}%)")
        
        with_pool_count += batch_with_pool
        without_pool_count += batch_without_pool
        with_trade_data += batch_with_trade
        total_sampled += len(data)
        
    except Exception as e:
        print(f"     Error: {e}")

# Calculate estimates
if total_sampled > 0:
    pool_percentage = (with_pool_count / total_sampled) * 100
    trade_percentage = (with_trade_data / total_sampled) * 100
    
    estimated_with_pool = int((with_pool_count / total_sampled) * total_counted)
    estimated_without_pool = total_counted - estimated_with_pool
    estimated_with_trade = int((with_trade_data / total_sampled) * total_counted)
    
    print(f"\n{'='*60}")
    print(f"FINAL SUMMARY:")
    print(f"Total calls in database: {total_counted:,}")
    print(f"Estimated with pool_address: {estimated_with_pool:,} ({pool_percentage:.1f}%)")
    print(f"Estimated missing pool_address: {estimated_without_pool:,} ({100-pool_percentage:.1f}%)")
    print(f"Estimated with KROM trade data: {estimated_with_trade:,} ({trade_percentage:.1f}%)")
    
    print(f"\nNEXT ACTIONS:")
    if estimated_without_pool > 0:
        print(f"1. 🔧 Populate pool_address for {estimated_without_pool:,} remaining calls")
    if estimated_with_pool > 0:
        print(f"2. ✅ {estimated_with_pool:,} calls ready for current price fetching")
    if estimated_with_trade > 0:
        ready_for_tracking = min(estimated_with_pool, estimated_with_trade)
        print(f"3. 🎯 ~{ready_for_tracking:,} calls ready for full price tracking!")