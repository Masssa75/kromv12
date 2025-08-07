#!/usr/bin/env python3
import requests
import json
import time
from datetime import datetime
import os
from dotenv import load_dotenv
import concurrent.futures
from threading import Lock

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
GECKO_API_KEY = os.getenv('GECKO_TERMINAL_API_KEY')

print("Fast ATH Recalculation Script")
print("=" * 60)
if GECKO_API_KEY:
    print(f"✅ Using PAID GeckoTerminal API (500 req/min)")
    print(f"   API Key: {GECKO_API_KEY[:10]}...")
else:
    print("⚠️ Using FREE GeckoTerminal API (30 req/min)")
print("=" * 60)

headers = {
    "apikey": SUPABASE_SERVICE_KEY,
    "Content-Type": "application/json"
}

# Stats tracking
stats_lock = Lock()
stats = {
    'updated': 0,
    'skipped': 0,
    'errors': 0,
    'processed': 0
}

def process_token(token):
    """Process a single token and return result"""
    global stats
    
    ticker = token['ticker']
    network = token['network']
    pool_address = token['pool_address']
    price_at_call = token['price_at_call']
    current_ath = token.get('ath_price', 0)
    current_ath_roi = token.get('ath_roi_percent', 0)
    
    # Map network names for GeckoTerminal
    network_map = {
        'ethereum': 'eth',
        'solana': 'solana',
        'bsc': 'bsc',
        'polygon': 'polygon',
        'arbitrum': 'arbitrum',
        'base': 'base',
        'avalanche': 'avalanche-c'
    }
    
    gecko_network = network_map.get(network, network)
    
    try:
        # Fetch OHLCV data from GeckoTerminal with API key
        url = f"https://api.geckoterminal.com/api/v2/networks/{gecko_network}/pools/{pool_address}/ohlcv/day"
        params = {"aggregate": 1, "limit": 1000, "currency": "usd"}
        headers = {"x-cg-pro-api-key": GECKO_API_KEY} if GECKO_API_KEY else {}
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code != 200:
            with stats_lock:
                stats['errors'] += 1
            return f"  ⚠️ {ticker}: API error {response.status_code}"
        
        data = response.json()
        ohlcv_list = data.get("data", {}).get("attributes", {}).get("ohlcv_list", [])
        
        if not ohlcv_list:
            with stats_lock:
                stats['skipped'] += 1
            return f"  ⏭️ {ticker}: No OHLCV data"
        
        # Parse call timestamp
        call_timestamp = token.get('buy_timestamp') or token.get('created_at')
        if call_timestamp:
            call_str = call_timestamp.replace("+00:00", "").split(".")[0]
            call_dt = datetime.strptime(call_str, "%Y-%m-%dT%H:%M:%S")
            call_unix = int(call_dt.timestamp())
        else:
            call_unix = 0
        
        # Find ATH after call
        max_high = 0
        max_timestamp = None
        
        for candle in ohlcv_list:
            timestamp, open_price, high, low, close, volume = candle
            
            if timestamp >= call_unix and high > max_high:
                max_high = high
                max_timestamp = timestamp
        
        if max_high > 0 and max_high > current_ath * 1.01:  # 1% tolerance
            calculated_roi = ((max_high - price_at_call) / price_at_call) * 100
            
            # Update the database
            update_url = f"{SUPABASE_URL}/rest/v1/crypto_calls?id=eq.{token['id']}"
            update_data = {
                "ath_price": max_high,
                "ath_roi_percent": max(0, calculated_roi),  # Never negative
                "ath_timestamp": datetime.fromtimestamp(max_timestamp).isoformat() + "Z"
            }
            
            update_response = requests.patch(update_url, headers=headers, json=update_data)
            
            if update_response.status_code in [200, 204]:
                with stats_lock:
                    stats['updated'] += 1
                return f"  ✅ {ticker}: Updated ATH ${current_ath:.6f} → ${max_high:.6f} ({calculated_roi:.0f}% ROI)"
            else:
                with stats_lock:
                    stats['errors'] += 1
                return f"  ❌ {ticker}: Update failed"
        else:
            with stats_lock:
                stats['skipped'] += 1
            return f"  ✓ {ticker}: ATH OK (${current_ath:.6f})"
            
    except Exception as e:
        with stats_lock:
            stats['errors'] += 1
        return f"  ❌ {ticker}: {str(e)[:50]}"
    finally:
        with stats_lock:
            stats['processed'] += 1

# Fetch all non-dead tokens with pool addresses
print("Fetching tokens from database...")
all_tokens = []
offset = 0
batch_size = 1000

while True:
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    params = f"?select=id,ticker,network,pool_address,price_at_call,ath_price,ath_roi_percent,buy_timestamp,created_at"
    params += f"&is_dead=eq.false&order=ath_roi_percent.desc.nullslast&limit={batch_size}&offset={offset}"
    
    response = requests.get(url + params, headers=headers)
    if response.status_code == 200:
        batch = response.json()
        valid_batch = [t for t in batch if t.get('pool_address') and t.get('price_at_call')]
        all_tokens.extend(valid_batch)
        
        if len(batch) < batch_size:
            break
        offset += batch_size
    else:
        print(f"Error: {response.status_code}")
        break

print(f"Found {len(all_tokens)} tokens to process")
print("-" * 60)

# Process tokens in parallel with rate limiting
if GECKO_API_KEY:
    print("Processing tokens with PAID API (500 req/min rate limit)...")
    batch_size = 80  # Process 80 at a time (500/min = ~8/sec, so 80 per 10 seconds)
    delay_between_batches = 10  # 10 seconds between batches
else:
    print("Processing tokens with FREE API (30 req/min rate limit)...")
    batch_size = 30
    delay_between_batches = 60  # 60 seconds between batches

results = []

# Process in batches
for i in range(0, len(all_tokens), batch_size):
    batch = all_tokens[i:i+batch_size]
    
    # Process batch in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        batch_results = list(executor.map(process_token, batch))
    
    # Print results
    for result in batch_results:
        if "✅" in result or "⚠️" in result or "❌" in result:
            print(result)
    
    # Progress update
    if stats['processed'] % 100 == 0 or stats['processed'] == len(all_tokens):
        print(f"\n📊 Progress: {stats['processed']}/{len(all_tokens)} | Updated: {stats['updated']} | Skipped: {stats['skipped']} | Errors: {stats['errors']}\n")
    
    # Rate limiting based on API tier
    if i + batch_size < len(all_tokens):
        time.sleep(delay_between_batches)

print("\n" + "=" * 60)
print("FINAL SUMMARY")
print("=" * 60)
print(f"Total processed: {stats['processed']}")
print(f"✅ Updated: {stats['updated']}")
print(f"⏭️ Skipped: {stats['skipped']}")
print(f"❌ Errors: {stats['errors']}")
print("\nScript completed!")