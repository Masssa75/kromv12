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

def count_records_with_price_data():
    """Count how many records have price data"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += f"?select=krom_id"
    url += f"&or=(price_at_call.not.is.null,current_price.not.is.null,ath_price.not.is.null)"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    req.add_header('Range', '0-10000')  # Get count
    req.add_header('Prefer', 'count=exact')
    
    try:
        response = urllib.request.urlopen(req)
        content_range = response.headers.get('content-range')
        if content_range:
            # Format: "0-X/total"
            total = int(content_range.split('/')[-1])
            return total
        else:
            data = json.loads(response.read().decode())
            return len(data)
    except Exception as e:
        print(f"Error counting records: {e}")
        return 0

def get_calls_with_price_data(limit=500, offset=0):
    """Get calls that have price data"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += f"?select=krom_id,ticker,created_at,price_at_call,current_price,ath_price"
    url += f"&or=(price_at_call.not.is.null,current_price.not.is.null,ath_price.not.is.null)"
    url += f"&order=created_at.asc"
    url += f"&limit={limit}"
    url += f"&offset={offset}"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching calls: {e}")
        return []

def clear_price_data_batch(krom_ids):
    """Clear price data for multiple calls at once"""
    cleared_count = 0
    failed_count = 0
    
    for krom_id in krom_ids:
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
        
        try:
            response = urllib.request.urlopen(req)
            if response.status == 200:
                cleared_count += 1
            else:
                failed_count += 1
        except Exception as e:
            print(f"Error clearing {krom_id}: {e}")
            failed_count += 1
    
    return cleared_count, failed_count

print("=== Clear ALL Remaining Price Data ===")
print(f"Started at: {datetime.now()}\n")

# First, count how many records have price data
print("Counting records with price data...")
total_with_price = count_records_with_price_data()
print(f"Total records with price data: {total_with_price}")

# Since we already cleared 100, calculate remaining
remaining = total_with_price
print(f"Records to clear: {remaining}")

if remaining == 0:
    print("\nNo records with price data found!")
else:
    print("\n" + "="*60)
    print(f"This will clear price data for ALL {remaining} remaining records")
    print("But preserve: raw_data, analysis scores, comments, etc.")
    print("="*60)
    
    # Auto-confirm for automation
    print("\nProceeding with clearing all remaining price data...")
    
    batch_size = 50
    total_cleared = 0
    total_failed = 0
    batch_num = 0
    
    # Process already cleared records (skip first 100)
    skip_offset = 0  # We'll process all records with price data
    
    while True:
        batch_num += 1
        print(f"\nProcessing batch {batch_num} (records {skip_offset + 1} to {skip_offset + batch_size})...")
        
        # Get next batch
        calls = get_calls_with_price_data(limit=batch_size, offset=skip_offset)
        
        if not calls:
            print("No more records to process")
            break
        
        # Extract krom_ids
        krom_ids = [call['krom_id'] for call in calls]
        
        # Clear this batch
        cleared, failed = clear_price_data_batch(krom_ids)
        total_cleared += cleared
        total_failed += failed
        
        print(f"  Batch {batch_num}: Cleared {cleared}, Failed {failed}")
        
        # Show some tickers from this batch
        sample_tickers = [call.get('ticker', 'Unknown') for call in calls[:5]]
        if len(calls) > 5:
            print(f"  Tickers: {', '.join(sample_tickers)}, and {len(calls) - 5} more...")
        else:
            print(f"  Tickers: {', '.join(sample_tickers)}")
        
        skip_offset += batch_size
        
        # Progress update every 5 batches
        if batch_num % 5 == 0:
            print(f"\n--- Progress: {total_cleared} cleared so far ---")
    
    print(f"\n{'='*60}")
    print(f"=== FINAL SUMMARY ===")
    print(f"Total records processed: {total_cleared + total_failed}")
    print(f"Successfully cleared: {total_cleared}")
    print(f"Failed: {total_failed}")
    print(f"{'='*60}")
    
    # Verify final count
    print("\nVerifying final state...")
    final_count = count_records_with_price_data()
    print(f"Records with price data after clearing: {final_count}")

print(f"\nFinished at: {datetime.now()}")