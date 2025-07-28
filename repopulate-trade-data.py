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

def main():
    print("=== Trade Data Repopulation Script ===")
    print(f"Started at: {datetime.now()}")
    
    # Configuration
    BATCH_SIZE = 100
    API_DELAY = 0.5  # Delay between API calls to avoid rate limits
    
    # First, let's see how many calls need updating
    test_batch = get_calls_without_trade(limit=1)
    if not test_batch:
        print("No calls found that need trade data!")
        return
    
    # Process in batches
    offset = 0
    total_processed = 0
    total_updated = 0
    total_failed = 0
    
    while True:
        print(f"\n--- Batch starting at offset {offset} ---")
        
        # Get batch of calls without trade data
        calls = get_calls_without_trade(limit=BATCH_SIZE, offset=offset)
        
        if not calls:
            print("No more calls to process!")
            break
        
        print(f"Processing {len(calls)} calls...")
        
        for i, call in enumerate(calls):
            krom_id = call['krom_id']
            ticker = call['ticker']
            
            print(f"\n[{i+1}/{len(calls)}] Processing {ticker} ({krom_id})...", end='', flush=True)
            
            # Fetch from KROM API
            krom_data = fetch_from_krom_api(krom_id)
            
            if krom_data and 'trade' in krom_data:
                # Update Supabase
                if update_supabase_raw_data(krom_id, krom_data):
                    print(f" ✅ Updated with buyPrice: ${krom_data['trade'].get('buyPrice', 'N/A')}")
                    total_updated += 1
                else:
                    print(" ❌ Failed to update")
                    total_failed += 1
            else:
                print(" ⚠️  No trade data from API")
                total_failed += 1
            
            total_processed += 1
            
            # Rate limiting
            time.sleep(API_DELAY)
            
            # Progress update every 10 items
            if (i + 1) % 10 == 0:
                print(f"\nProgress: {total_processed} processed, {total_updated} updated, {total_failed} failed")
        
        # Move to next batch
        offset += BATCH_SIZE
        
        # Ask to continue after each batch
        if input(f"\nContinue with next batch? (y/n): ").lower() != 'y':
            break
    
    print(f"\n=== Summary ===")
    print(f"Total processed: {total_processed}")
    print(f"Successfully updated: {total_updated}")
    print(f"Failed: {total_failed}")
    print(f"Completed at: {datetime.now()}")

if __name__ == "__main__":
    # Test mode - just do 5 calls
    print("\n🧪 TEST MODE - Processing only 5 calls")
    print("Run with --full to process all calls\n")
    
    import sys
    if '--full' in sys.argv:
        main()
    else:
        # Test with just 5 calls
        calls = get_calls_without_trade(limit=5)
        print(f"Found {len(calls)} calls without trade data:\n")
        
        for call in calls:
            print(f"- {call['ticker']} ({call['krom_id']})")
        
        if input("\nTest update these 5 calls? (y/n): ").lower() == 'y':
            for call in calls:
                print(f"\nTesting {call['ticker']}...")
                krom_data = fetch_from_krom_api(call['krom_id'])
                if krom_data:
                    has_trade = 'trade' in krom_data
                    print(f"  KROM API has trade data: {has_trade}")
                    if has_trade:
                        print(f"  Buy price: ${krom_data['trade'].get('buyPrice', 'N/A')}")
                else:
                    print("  Failed to fetch from KROM API")