import json
import urllib.request
import os
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

def get_calls_without_trade_data():
    """Get calls from Supabase that still don't have trade data"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += f"?select=krom_id,ticker"
    url += f"&raw_data->>trade=is.null"
    url += f"&order=created_at.desc"
    url += f"&limit=100"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching calls: {e}")
        return []

def fetch_latest_100_from_krom():
    """Fetch the latest 100 calls from KROM API"""
    url = "https://krom.one/api/v1/calls"
    
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {KROM_API_TOKEN}')
    
    try:
        response = urllib.request.urlopen(req)
        return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching from KROM: {e}")
        return []

def update_supabase(krom_id, raw_data):
    """Update Supabase with complete raw_data"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls?krom_id=eq.{krom_id}"
    
    data = json.dumps({
        "raw_data": raw_data
    }).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, method='PATCH')
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')
    req.add_header('Content-Type', 'application/json')
    req.add_header('Prefer', 'return=minimal')
    
    try:
        response = urllib.request.urlopen(req)
        return response.status == 204
    except Exception as e:
        print(f"Error updating {krom_id}: {e}")
        return False

print("=== Checking for Missing Data - 5 API Calls ===")
print(f"Started at: {datetime.now()}\n")

# Get calls that still need trade data
print("Getting calls without trade data...")
missing_calls = get_calls_without_trade_data()

# Create a set of IDs we're looking for
missing_ids = {call['krom_id']: call['ticker'] for call in missing_calls}
print(f"Found {len(missing_ids)} calls still missing trade data\n")

if len(missing_ids) == 0:
    print("All calls have trade data!")
else:
    # Show which ones are missing
    print("Missing trade data for:")
    for krom_id, ticker in list(missing_ids.items())[:20]:  # Show first 20
        print(f"  - {ticker} ({krom_id})")
    if len(missing_ids) > 20:
        print(f"  ... and {len(missing_ids) - 20} more")
    print()

    # Track what we find across all attempts
    found_in_attempt = {i: [] for i in range(1, 6)}
    all_krom_data = {}
    
    # Run 5 API calls
    for attempt in range(1, 6):
        print(f"\n=== Attempt {attempt}/5 ===")
        print("Fetching from KROM API...")
        
        krom_calls = fetch_latest_100_from_krom()
        print(f"Received {len(krom_calls)} calls")
        
        # Check what IDs we got
        krom_ids_in_response = set()
        for call in krom_calls:
            call_id = call.get('_id') or call.get('id')
            if call_id:
                krom_ids_in_response.add(call_id)
                # Store the data if it's one we're looking for
                if call_id in missing_ids:
                    all_krom_data[call_id] = call
        
        # See if any missing ones appeared
        found_this_time = []
        for missing_id in missing_ids:
            if missing_id in krom_ids_in_response:
                found_this_time.append(missing_id)
        
        if found_this_time:
            print(f"✅ Found {len(found_this_time)} missing calls:")
            for krom_id in found_this_time:
                ticker = missing_ids[krom_id]
                krom_data = all_krom_data[krom_id]
                has_trade = 'trade' in krom_data
                print(f"   - {ticker} (has trade: {has_trade})")
                found_in_attempt[attempt].append((krom_id, ticker, has_trade))
        else:
            print("❌ None of the missing calls appeared in this response")
        
        # Show some stats about the response
        oldest_timestamp = min(call.get('timestamp', 0) for call in krom_calls)
        newest_timestamp = max(call.get('timestamp', 0) for call in krom_calls)
        
        if oldest_timestamp and newest_timestamp:
            oldest_date = datetime.fromtimestamp(oldest_timestamp)
            newest_date = datetime.fromtimestamp(newest_timestamp)
            print(f"Response time range: {oldest_date} to {newest_date}")
        
        # Wait a bit before next call
        if attempt < 5:
            time.sleep(2)
    
    # Summary
    print(f"\n=== Summary After 5 Attempts ===")
    
    total_found = len(all_krom_data)
    if total_found > 0:
        print(f"\nFound {total_found} of the {len(missing_ids)} missing calls across all attempts")
        
        # Update the found ones
        print("\nUpdating found calls...")
        updated_count = 0
        for krom_id, krom_data in all_krom_data.items():
            ticker = missing_ids[krom_id]
            if update_supabase(krom_id, krom_data):
                if 'trade' in krom_data:
                    buy_price = krom_data['trade'].get('buyPrice', 'N/A')
                    print(f"  ✅ Updated {ticker} with buy price: ${buy_price}")
                else:
                    print(f"  ✅ Updated {ticker} (no trade data)")
                updated_count += 1
            else:
                print(f"  ❌ Failed to update {ticker}")
        
        print(f"\nSuccessfully updated {updated_count} calls")
    else:
        print(f"\n❌ None of the {len(missing_ids)} missing calls appeared in any of the 5 API responses")
        print("\nThis suggests these calls are older than the most recent 100 calls returned by the API")

print(f"\nFinished at: {datetime.now()}")