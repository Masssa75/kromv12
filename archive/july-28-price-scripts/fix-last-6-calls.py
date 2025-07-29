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

# List of calls that have incorrect DOGSHIT data
calls_to_fix = [
    # Skip DOGSHIT as it's correct
    ('REMI', '6886d413eb25eec68caf837f'),
    ('SLOP', '6886d2cbeb25eec68caf82f3'),
    ('QUOKKA', '6886c482eb25eec68caf7e75'),
    ('SPURDO', '6886bc02eb25eec68caf7bf5'),
    ('NYAN', '6886a784eb25eec68caf75aa')
]

def clear_raw_data(krom_id):
    """Clear the incorrect raw_data"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls?krom_id=eq.{krom_id}"
    
    # First get the existing data
    req = urllib.request.Request(url + "&select=raw_data")
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        existing = json.loads(response.read().decode())
        
        if existing and existing[0].get('raw_data'):
            # Keep the raw_data but remove the trade object
            raw_data = existing[0]['raw_data']
            if 'trade' in raw_data:
                del raw_data['trade']
            
            # Update with modified raw_data
            data = json.dumps({"raw_data": raw_data}).encode('utf-8')
            
            update_req = urllib.request.Request(url, data=data, method='PATCH')
            update_req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
            update_req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')
            update_req.add_header('Content-Type', 'application/json')
            update_req.add_header('Prefer', 'return=minimal')
            
            update_response = urllib.request.urlopen(update_req)
            return update_response.status == 204
    except Exception as e:
        print(f"Error clearing {krom_id}: {e}")
        return False

def fetch_and_update(krom_id, ticker, timestamp):
    """Fetch correct data from KROM API and update"""
    # Fetch from KROM API using pagination
    url = f"https://krom.one/api/v1/calls?beforeTimestamp={timestamp + 100}"
    
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {KROM_API_TOKEN}')
    
    try:
        response = urllib.request.urlopen(req)
        calls = json.loads(response.read().decode())
        
        # Search for our specific call
        for call in calls:
            if call.get('_id') == krom_id or call.get('id') == krom_id:
                # Verify ticker matches
                api_ticker = call.get('token', {}).get('symbol', 'N/A')
                if api_ticker == ticker:
                    # Update Supabase
                    update_url = f"{SUPABASE_URL}/rest/v1/crypto_calls?krom_id=eq.{krom_id}"
                    data = json.dumps({"raw_data": call}).encode('utf-8')
                    
                    update_req = urllib.request.Request(update_url, data=data, method='PATCH')
                    update_req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
                    update_req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')
                    update_req.add_header('Content-Type', 'application/json')
                    update_req.add_header('Prefer', 'return=minimal')
                    
                    update_response = urllib.request.urlopen(update_req)
                    if update_response.status == 204:
                        buy_price = call.get('trade', {}).get('buyPrice', 'No trade data')
                        return True, buy_price
                    else:
                        return False, "Update failed"
                else:
                    return False, f"Ticker mismatch: {api_ticker}"
        
        return False, "Not found in KROM response"
        
    except Exception as e:
        return False, f"Error: {e}"

print("=== Fixing Last 6 Calls with Correct Data ===")
print(f"Started at: {datetime.now()}\n")

# First, get timestamps for each call
print("Step 1: Getting timestamps for each call...")

timestamps = {}
for ticker, krom_id in calls_to_fix:
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls?krom_id=eq.{krom_id}&select=created_at,raw_data"
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        if data:
            # Try to get timestamp from raw_data first
            raw_data = data[0].get('raw_data', {})
            if raw_data and raw_data.get('timestamp'):
                timestamps[krom_id] = raw_data['timestamp']
            else:
                # Fallback to created_at
                created_at = data[0].get('created_at', '2025-01-01T00:00:00Z')
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                timestamps[krom_id] = int(dt.timestamp())
            
            print(f"  {ticker}: timestamp {timestamps[krom_id]}")
    except Exception as e:
        print(f"  {ticker}: Error getting timestamp - {e}")

print("\nStep 2: Clearing incorrect trade data...")

for ticker, krom_id in calls_to_fix:
    if clear_raw_data(krom_id):
        print(f"  ✅ Cleared incorrect trade data for {ticker}")
    else:
        print(f"  ❌ Failed to clear data for {ticker}")

print("\nStep 3: Fetching and updating with correct data...")

for ticker, krom_id in calls_to_fix:
    if krom_id in timestamps:
        print(f"\nProcessing {ticker} (ID: {krom_id})...")
        success, result = fetch_and_update(krom_id, ticker, timestamps[krom_id])
        
        if success:
            print(f"  ✅ Updated with buy price: ${result}")
        else:
            print(f"  ❌ Failed: {result}")
        
        # Rate limiting
        time.sleep(0.5)
    else:
        print(f"\nSkipping {ticker} - no timestamp available")

print(f"\n✅ Process completed at: {datetime.now()}")
print("\nRefresh the UI to see the corrected buy prices!")