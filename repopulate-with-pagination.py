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

def get_calls_needing_update(limit=5):
    """Get calls from Supabase that need trade data"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += f"?select=krom_id,ticker,created_at,buy_timestamp,raw_data"
    url += f"&raw_data->>trade=is.null"
    url += f"&order=created_at.desc"
    url += f"&limit={limit}"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching calls: {e}")
        return []

def fetch_from_krom_around_timestamp(timestamp, target_ids):
    """Fetch calls from KROM API around a specific timestamp"""
    found_calls = {}
    
    # Try fetching before this timestamp
    url = f"https://krom.one/api/v1/calls?beforeTimestamp={timestamp + 100}"  # Add 100 seconds buffer
    
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {KROM_API_TOKEN}')
    
    try:
        response = urllib.request.urlopen(req)
        calls = json.loads(response.read().decode())
        
        # Search through results for our target IDs
        for call in calls:
            call_id = call.get('_id') or call.get('id')
            if call_id in target_ids:
                found_calls[call_id] = call
                print(f"    ✅ Found {call.get('token', {}).get('symbol', 'N/A')} (ID: {call_id})")
        
        return found_calls
        
    except Exception as e:
        print(f"    ❌ Error fetching from KROM: {e}")
        return {}

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

print("=== Smart Repopulation with Pagination ===")
print(f"Started at: {datetime.now()}\n")

# Get calls that need updating
calls_to_update = get_calls_needing_update(limit=5)

if not calls_to_update:
    print("No calls found that need trade data!")
else:
    print(f"Found {len(calls_to_update)} calls to update:\n")
    
    # Group calls by approximate timestamp (within same time window)
    grouped_calls = {}
    
    for call in calls_to_update:
        krom_id = call['krom_id']
        ticker = call['ticker']
        
        # Get timestamp from raw_data if available, otherwise use created_at
        if call.get('raw_data') and call['raw_data'].get('timestamp'):
            timestamp = call['raw_data']['timestamp']
        else:
            # Convert created_at to unix timestamp
            created_at = call.get('created_at', '2025-01-01T00:00:00Z')
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            timestamp = int(dt.timestamp())
        
        print(f"- {ticker} (ID: {krom_id}, Timestamp: {timestamp})")
        
        # Group by 1000-second windows
        time_window = timestamp // 1000
        if time_window not in grouped_calls:
            grouped_calls[time_window] = []
        grouped_calls[time_window].append({
            'krom_id': krom_id,
            'ticker': ticker,
            'timestamp': timestamp
        })
    
    print(f"\nGrouped into {len(grouped_calls)} time windows")
    
    # Process each group
    total_updated = 0
    for time_window, calls in grouped_calls.items():
        print(f"\nProcessing time window around {time_window * 1000}...")
        
        # Get all IDs in this group
        target_ids = [c['krom_id'] for c in calls]
        
        # Use the earliest timestamp in the group
        earliest_timestamp = min(c['timestamp'] for c in calls)
        
        # Fetch from KROM API
        found_data = fetch_from_krom_around_timestamp(earliest_timestamp, target_ids)
        
        # Update Supabase for found calls
        for call in calls:
            krom_id = call['krom_id']
            ticker = call['ticker']
            
            if krom_id in found_data:
                raw_data = found_data[krom_id]
                
                # Verify it's the right token
                api_ticker = raw_data.get('token', {}).get('symbol', 'N/A')
                if api_ticker == ticker:
                    if update_supabase(krom_id, raw_data):
                        if 'trade' in raw_data:
                            buy_price = raw_data['trade'].get('buyPrice', 'N/A')
                            print(f"    ✅ Updated {ticker} with buy price: ${buy_price}")
                        else:
                            print(f"    ✅ Updated {ticker} (no trade data)")
                        total_updated += 1
                    else:
                        print(f"    ❌ Failed to update {ticker}")
                else:
                    print(f"    ⚠️  Ticker mismatch for {krom_id}: expected {ticker}, got {api_ticker}")
            else:
                print(f"    ❌ {ticker} not found in KROM response")
        
        # Rate limiting
        time.sleep(0.5)
    
    print(f"\n✅ Completed: {total_updated}/{len(calls_to_update)} calls updated")
    print(f"Finished at: {datetime.now()}")