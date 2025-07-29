import json
import urllib.request
import urllib.error
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

def get_calls_without_trade(limit=100, offset=0):
    """Get calls from Supabase that don't have trade data"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += f"?select=krom_id,ticker,created_at"
    url += f"&raw_data->>trade=is.null"  # Only get calls without trade data
    url += f"&order=created_at.desc"
    url += f"&limit={limit}&offset={offset}"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')
    
    try:
        response = urllib.request.urlopen(req)
        return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching calls: {e}")
        return []

def fetch_from_krom_api(krom_id):
    """Fetch single call data from KROM API"""
    # Try different endpoints
    endpoints = [
        f"https://krom.one/api/v1/calls/{krom_id}",
        f"https://krom.one/api/v1/calls?id={krom_id}"
    ]
    
    for url in endpoints:
        req = urllib.request.Request(url)
        req.add_header('Authorization', f'Bearer {KROM_API_TOKEN}')
        
        try:
            response = urllib.request.urlopen(req)
            data = response.read().decode()
            
            # Parse response
            result = json.loads(data)
            
            # Handle array response
            if isinstance(result, list) and len(result) > 0:
                return result[0]
            # Handle object response
            elif isinstance(result, dict):
                return result
                
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue  # Try next endpoint
            else:
                print(f"HTTP Error {e.code} for {krom_id}: {e.reason}")
                return None
        except Exception as e:
            print(f"Error fetching {krom_id}: {e}")
            continue
    
    return None

def update_supabase_raw_data(krom_id, raw_data):
    """Update raw_data in Supabase"""
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

# Process just 5 recent entries
print("=== Trade Data Repopulation - Test Run ===")
print(f"Started at: {datetime.now()}")
print("\nFetching 5 recent calls without trade data...\n")

calls = get_calls_without_trade(limit=5)

if not calls:
    print("No calls found that need trade data!")
else:
    print(f"Found {len(calls)} calls to process:\n")
    
    for call in calls:
        print(f"- {call['ticker']} ({call['krom_id']})")
    
    print("\nStarting repopulation...\n")
    
    API_DELAY = 0.5  # Delay between API calls
    
    for i, call in enumerate(calls):
        krom_id = call['krom_id']
        ticker = call['ticker']
        
        print(f"[{i+1}/5] Processing {ticker} ({krom_id})...", end='', flush=True)
        
        # Fetch from KROM API
        krom_data = fetch_from_krom_api(krom_id)
        
        if krom_data and 'trade' in krom_data:
            # Update Supabase
            if update_supabase_raw_data(krom_id, krom_data):
                print(f" ✅ Updated with buyPrice: ${krom_data['trade'].get('buyPrice', 'N/A')}")
            else:
                print(" ❌ Failed to update")
        else:
            print(" ⚠️  No trade data from API")
        
        # Rate limiting
        time.sleep(API_DELAY)
    
    print(f"\n✅ Test run completed at: {datetime.now()}")
    print("\nNow refresh the UI to see if the buy prices appear for these tokens!")