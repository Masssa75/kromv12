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

def get_last_6_calls():
    """Get the last 6 calls from Supabase including DOGSHIT"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += f"?select=krom_id,ticker,created_at,raw_data"
    url += f"&order=created_at.desc"
    url += f"&limit=6"
    
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
    
    # Try fetching before this timestamp with buffer
    url = f"https://krom.one/api/v1/calls?beforeTimestamp={timestamp + 100}"
    
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {KROM_API_TOKEN}')
    
    try:
        response = urllib.request.urlopen(req)
        calls = json.loads(response.read().decode())
        
        print(f"    Fetched {len(calls)} calls from KROM API")
        
        # Search through results for our target IDs
        for call in calls:
            call_id = call.get('_id') or call.get('id')
            if call_id in target_ids:
                found_calls[call_id] = call
                ticker = call.get('token', {}).get('symbol', 'N/A')
                print(f"    ✅ Found {ticker} (ID: {call_id})")
        
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

print("=== Repopulating Last 6 Calls (Starting with DOGSHIT) ===")
print(f"Started at: {datetime.now()}\n")

# Get the last 6 calls
calls = get_last_6_calls()

if not calls:
    print("No calls found!")
else:
    print(f"Found {len(calls)} recent calls:\n")
    
    # Show what we're going to update
    for i, call in enumerate(calls):
        krom_id = call['krom_id']
        ticker = call['ticker']
        raw_data = call.get('raw_data', {})
        
        has_trade = bool(raw_data) and 'trade' in raw_data
        
        print(f"{i+1}. {ticker} (ID: {krom_id})")
        if has_trade:
            buy_price = raw_data.get('trade', {}).get('buyPrice', 'N/A')
            print(f"   Already has trade data - Buy price: ${buy_price}")
        else:
            print(f"   Missing trade data - needs update")
    
    print("\nStarting repopulation process...\n")
    
    # Group calls by timestamp windows
    grouped_calls = {}
    
    for call in calls:
        krom_id = call['krom_id']
        ticker = call['ticker']
        raw_data = call.get('raw_data', {})
        
        # Skip if already has trade data
        if raw_data and 'trade' in raw_data:
            print(f"Skipping {ticker} - already has trade data")
            continue
        
        # Get timestamp
        if raw_data and raw_data.get('timestamp'):
            timestamp = raw_data['timestamp']
        else:
            # Use created_at as fallback
            created_at = call.get('created_at', '2025-01-01T00:00:00Z')
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            timestamp = int(dt.timestamp())
        
        # Group by time windows
        time_window = timestamp // 1000
        if time_window not in grouped_calls:
            grouped_calls[time_window] = []
        
        grouped_calls[time_window].append({
            'krom_id': krom_id,
            'ticker': ticker,
            'timestamp': timestamp
        })
    
    if not grouped_calls:
        print("All calls already have trade data!")
    else:
        print(f"Processing {sum(len(calls) for calls in grouped_calls.values())} calls in {len(grouped_calls)} time windows\n")
        
        total_updated = 0
        
        for time_window, window_calls in grouped_calls.items():
            print(f"Processing time window around timestamp {time_window * 1000}...")
            
            # Get all IDs in this group
            target_ids = [c['krom_id'] for c in window_calls]
            
            # Use the earliest timestamp in the group
            earliest_timestamp = min(c['timestamp'] for c in window_calls)
            
            # Fetch from KROM API
            found_data = fetch_from_krom_around_timestamp(earliest_timestamp, target_ids)
            
            # Update each call
            for call in window_calls:
                krom_id = call['krom_id']
                ticker = call['ticker']
                
                if krom_id in found_data:
                    raw_data = found_data[krom_id]
                    
                    # Verify ticker matches
                    api_ticker = raw_data.get('token', {}).get('symbol', 'N/A')
                    if api_ticker == ticker:
                        if update_supabase(krom_id, raw_data):
                            if 'trade' in raw_data:
                                buy_price = raw_data['trade'].get('buyPrice', 'N/A')
                                print(f"    ✅ Updated {ticker} with buy price: ${buy_price}")
                            else:
                                print(f"    ✅ Updated {ticker} (no trade data in API)")
                            total_updated += 1
                        else:
                            print(f"    ❌ Failed to update {ticker}")
                    else:
                        print(f"    ⚠️  Ticker mismatch for {krom_id}: expected {ticker}, got {api_ticker}")
                else:
                    print(f"    ❌ {ticker} not found in KROM response")
            
            # Rate limiting
            time.sleep(0.5)
        
        print(f"\n✅ Completed: {total_updated} calls updated")
    
    print(f"\nFinished at: {datetime.now()}")
    print("\nRefresh the UI to see the updated buy prices!")