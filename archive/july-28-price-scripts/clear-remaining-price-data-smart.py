import json
import urllib.request
import os
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

def get_all_calls_with_price_data():
    """Get ALL calls that have price data without pagination limits"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += f"?select=krom_id,ticker,created_at,price_at_call,current_price,ath_price"
    url += f"&or=(price_at_call.not.is.null,current_price.not.is.null,ath_price.not.is.null)"
    url += f"&order=created_at.asc"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    req.add_header('Range', '0-10000')  # Get all
    
    try:
        response = urllib.request.urlopen(req)
        return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching calls: {e}")
        return []

def clear_price_data(krom_id):
    """Clear all price-related fields for a specific call"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls?krom_id=eq.{krom_id}"
    
    # Set all price fields to null
    clear_data = {
        "price_at_call": None,
        "current_price": None,
        "ath_price": None,
        "ath_timestamp": None,
        "roi_percent": None,
        "ath_roi_percent": None,
        "market_cap_at_call": None,
        "current_market_cap": None,
        "ath_market_cap": None,
        "fdv_at_call": None,
        "current_fdv": None,
        "ath_fdv": None,
        "price_fetched_at": None,
        "price_network": None,
        "token_supply": None
    }
    
    data = json.dumps(clear_data).encode('utf-8')
    
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
        print(f"Error clearing {krom_id}: {e}")
        return False

print("=== Smart Clear ALL Remaining Price Data ===")
print(f"Started at: {datetime.now()}\n")

# Get all records with price data
print("Fetching all records with price data...")
calls_with_price = get_all_calls_with_price_data()
total_records = len(calls_with_price)

print(f"Found {total_records} records with price data")

if total_records == 0:
    print("\nNo records with price data found!")
else:
    # Group by date for better visibility
    dates = {}
    for call in calls_with_price:
        date = call.get('created_at', '')[:10]
        if date not in dates:
            dates[date] = 0
        dates[date] += 1
    
    print("\nRecords by date:")
    for date in sorted(dates.keys())[:10]:  # Show first 10 dates
        print(f"  {date}: {dates[date]} records")
    if len(dates) > 10:
        print(f"  ... and {len(dates) - 10} more dates")
    
    print("\n" + "="*60)
    print(f"This will clear price data for ALL {total_records} records")
    print("But preserve: raw_data, analysis scores, comments, etc.")
    print("="*60)
    
    print("\nProceeding with clearing...")
    
    cleared = 0
    failed = 0
    
    # Process in batches for progress updates
    batch_size = 50
    for i in range(0, total_records, batch_size):
        batch = calls_with_price[i:i+batch_size]
        batch_cleared = 0
        batch_failed = 0
        
        print(f"\nProcessing batch {i//batch_size + 1} (records {i+1} to {min(i+batch_size, total_records)})...")
        
        for call in batch:
            krom_id = call['krom_id']
            ticker = call.get('ticker', 'Unknown')
            
            if clear_price_data(krom_id):
                batch_cleared += 1
                cleared += 1
                if batch_cleared <= 3:  # Show first few
                    print(f"  ✅ Cleared {ticker}")
            else:
                batch_failed += 1
                failed += 1
                if batch_failed <= 3:  # Show first few failures
                    print(f"  ❌ Failed {ticker}")
        
        print(f"  Batch summary: {batch_cleared} cleared, {batch_failed} failed")
        
        # Progress update every 200 records
        if (i + batch_size) % 200 == 0:
            print(f"\n--- Overall progress: {cleared}/{total_records} cleared ---")
    
    print(f"\n{'='*60}")
    print(f"=== FINAL SUMMARY ===")
    print(f"Total records with price data: {total_records}")
    print(f"Successfully cleared: {cleared}")
    print(f"Failed: {failed}")
    print(f"Success rate: {cleared/total_records*100:.1f}%")
    print(f"{'='*60}")
    
    # Final verification
    print("\nVerifying final state...")
    remaining = get_all_calls_with_price_data()
    print(f"Records with price data after clearing: {len(remaining)}")
    
    if len(remaining) > 0:
        print(f"\nShowing first 5 remaining records:")
        for r in remaining[:5]:
            print(f"  - {r.get('ticker', 'Unknown')} ({r.get('krom_id', 'Unknown')})")

print(f"\nFinished at: {datetime.now()}")