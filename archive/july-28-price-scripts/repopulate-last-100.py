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

def get_last_100_calls():
    """Get the last 100 calls from Supabase"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += f"?select=krom_id,ticker,raw_data"
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

print("=== Repopulating Last 100 Calls ===")
print(f"Started at: {datetime.now()}\n")

# Get the last 100 calls from Supabase
print("Fetching last 100 calls from Supabase...")
supabase_calls = get_last_100_calls()
print(f"Found {len(supabase_calls)} calls in Supabase\n")

# Create a map of krom_id to call data
supabase_map = {call['krom_id']: call for call in supabase_calls}

# Count how many need updates
needs_update = 0
already_has_trade = 0

for call in supabase_calls:
    raw_data = call.get('raw_data', {})
    if not raw_data or 'trade' not in raw_data:
        needs_update += 1
    else:
        already_has_trade += 1

print(f"Status:")
print(f"- Already have trade data: {already_has_trade}")
print(f"- Need update: {needs_update}\n")

if needs_update == 0:
    print("All calls already have trade data!")
else:
    # Fetch the latest 100 from KROM API
    print("Fetching latest 100 calls from KROM API...")
    krom_calls = fetch_latest_100_from_krom()
    print(f"Received {len(krom_calls)} calls from KROM API\n")
    
    # Create a map of KROM calls by ID
    krom_map = {}
    for call in krom_calls:
        call_id = call.get('_id') or call.get('id')
        if call_id:
            krom_map[call_id] = call
    
    # Update matching calls
    updated = 0
    no_trade_data = 0
    not_found = 0
    ticker_mismatch = 0
    
    print("Updating calls...")
    
    for krom_id, supabase_call in supabase_map.items():
        # Skip if already has trade data
        raw_data = supabase_call.get('raw_data', {})
        if raw_data and 'trade' in raw_data:
            continue
        
        ticker = supabase_call['ticker']
        
        if krom_id in krom_map:
            krom_data = krom_map[krom_id]
            
            # Verify ticker matches
            api_ticker = krom_data.get('token', {}).get('symbol', 'N/A')
            
            if api_ticker == ticker:
                # Update Supabase
                if update_supabase(krom_id, krom_data):
                    if 'trade' in krom_data:
                        buy_price = krom_data['trade'].get('buyPrice', 'N/A')
                        print(f"  ✅ Updated {ticker} with buy price: ${buy_price}")
                        updated += 1
                    else:
                        print(f"  ✅ Updated {ticker} (no trade data in API)")
                        no_trade_data += 1
                else:
                    print(f"  ❌ Failed to update {ticker}")
            else:
                print(f"  ⚠️  Ticker mismatch for {ticker}: API shows {api_ticker}")
                ticker_mismatch += 1
        else:
            not_found += 1
            # Don't print for each one to avoid spam
    
    print(f"\n=== Summary ===")
    print(f"Total calls in Supabase: {len(supabase_calls)}")
    print(f"Already had trade data: {already_has_trade}")
    print(f"Needed updates: {needs_update}")
    print(f"Successfully updated with trade data: {updated}")
    print(f"Updated but no trade data in API: {no_trade_data}")
    print(f"Not found in KROM response: {not_found}")
    print(f"Ticker mismatches: {ticker_mismatch}")

print(f"\nFinished at: {datetime.now()}")
print("\nRefresh the UI to see the updated buy prices!")