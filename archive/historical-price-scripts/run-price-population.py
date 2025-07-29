#!/usr/bin/env python3
import subprocess
import time
import json
import urllib.request
from datetime import datetime

print("=== Automated Price Population Runner ===")
print(f"Started: {datetime.now()}")
print()

# Get service key
service_key = None
with open('.env', 'r') as f:
    for line in f:
        if line.startswith('SUPABASE_SERVICE_ROLE_KEY='):
            service_key = line.split('=', 1)[1].strip()
            break

def get_progress():
    """Get current progress of price population"""
    supabase_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/rest/v1/crypto_calls"
    
    # Total count
    total_req = urllib.request.Request(f"{supabase_url}?select=*", method='HEAD')
    total_req.add_header('apikey', service_key)
    total_req.add_header('Authorization', f'Bearer {service_key}')
    total_req.add_header('Prefer', 'count=exact')
    
    # Count with prices
    prices_req = urllib.request.Request(f"{supabase_url}?select=*&price_at_call=not.is.null", method='HEAD')
    prices_req.add_header('apikey', service_key)
    prices_req.add_header('Authorization', f'Bearer {service_key}')
    prices_req.add_header('Prefer', 'count=exact')
    
    try:
        total_resp = urllib.request.urlopen(total_req)
        total_count = int(total_resp.headers.get('content-range').split('/')[1])
        
        prices_resp = urllib.request.urlopen(prices_req)
        prices_count = int(prices_resp.headers.get('content-range').split('/')[1])
        
        return prices_count, total_count
    except:
        return 0, 0

# Run the script multiple times
runs = 0
max_runs = 50  # Maximum number of runs
max_time = 3600  # Maximum total time in seconds (1 hour)
start_time = time.time()

initial_count, total_count = get_progress()
print(f"📊 Initial state: {initial_count}/{total_count} tokens have prices ({initial_count/total_count*100:.1f}%)")
print(f"📊 Tokens remaining: {total_count - initial_count}")
print()

while runs < max_runs and (time.time() - start_time) < max_time:
    runs += 1
    print(f"\n{'='*60}")
    print(f"RUN {runs} - Starting at {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}")
    
    # Get current progress
    current_count, total_count = get_progress()
    print(f"Current progress: {current_count}/{total_count} ({current_count/total_count*100:.1f}%)")
    
    # Check if we're done
    if current_count >= total_count:
        print("\n✅ ALL TOKENS HAVE PRICES! Mission complete!")
        break
    
    # Run the batch processor
    try:
        # Run with 90 second timeout
        result = subprocess.run(
            ['python3', 'populate-historical-prices-using-created-at.py'],
            capture_output=True,
            text=True,
            timeout=90
        )
        
        if result.returncode == 0:
            print("✅ Batch completed successfully")
        else:
            print(f"⚠️ Batch exited with code {result.returncode}")
            
    except subprocess.TimeoutExpired:
        print("⏱️ Batch timed out (expected for large batches)")
    except Exception as e:
        print(f"❌ Error running batch: {e}")
    
    # Get new progress
    new_count, _ = get_progress()
    tokens_processed = new_count - current_count
    
    if tokens_processed > 0:
        print(f"📈 Processed {tokens_processed} tokens in this run")
        rate = tokens_processed / 90  # tokens per second
        remaining = total_count - new_count
        eta_seconds = remaining / rate if rate > 0 else 0
        eta_minutes = eta_seconds / 60
        print(f"⏱️ ETA: ~{eta_minutes:.0f} minutes at current rate")
    else:
        print("⚠️ No new tokens processed - may have hit rate limits")
        print("Waiting 30 seconds before next run...")
        time.sleep(30)
    
    # Small delay between runs
    time.sleep(2)

# Final summary
final_count, total_count = get_progress()
print(f"\n{'='*60}")
print("FINAL SUMMARY")
print(f"{'='*60}")
print(f"Total runs: {runs}")
print(f"Time elapsed: {(time.time() - start_time) / 60:.1f} minutes")
print(f"Initial progress: {initial_count}/{total_count} ({initial_count/total_count*100:.1f}%)")
print(f"Final progress: {final_count}/{total_count} ({final_count/total_count*100:.1f}%)")
print(f"Tokens processed: {final_count - initial_count}")

if final_count >= total_count:
    print("\n🎉 SUCCESS! All tokens now have historical prices!")
else:
    print(f"\n📊 Remaining tokens: {total_count - final_count}")
    print("Run this script again to continue processing.")

print(f"\nCompleted: {datetime.now()}")