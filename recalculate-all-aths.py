#!/usr/bin/env python3
import requests
import json
import time
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

print("ATH Recalculation Script")
print("=" * 60)
print("This script will recalculate ATH for all non-dead tokens")
print("Processing order: Highest ATH ROI first")
print("=" * 60)

# Fetch all non-dead tokens with existing ATH, ordered by highest ATH ROI first
headers = {
    "apikey": SUPABASE_SERVICE_KEY,
    "Content-Type": "application/json"
}

print("\nFetching tokens from database...")

# Fetch all tokens in batches - simpler approach
all_tokens = []
batch_size = 1000
offset = 0

# First get total count
while True:
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    params = f"?select=id,ticker,network,pool_address,price_at_call,ath_price,ath_roi_percent,buy_timestamp,created_at&is_dead=eq.false&order=ath_roi_percent.desc.nullslast&limit={batch_size}&offset={offset}"
    
    response = requests.get(url + params, headers=headers)
    if response.status_code == 200:
        batch = response.json()
        # Filter for tokens with pool_address and price_at_call
        valid_batch = [t for t in batch if t.get('pool_address') and t.get('price_at_call')]
        all_tokens.extend(valid_batch)
        print(f"  Fetched {len(valid_batch)} valid tokens (offset {offset})")
        
        if len(batch) < batch_size:
            break
        offset += batch_size
    else:
        print(f"Error fetching tokens: {response.status_code}")
        print(f"Response: {response.text}")
        break

print(f"Found {len(all_tokens)} non-dead tokens with pool addresses to process")

print(f"\nTotal tokens fetched: {len(all_tokens)}")

# Process each token
print("\nStarting ATH recalculation...")
print("-" * 60)

updated_count = 0
error_count = 0
skipped_count = 0

for idx, token in enumerate(all_tokens, 1):
    ticker = token['ticker']
    network = token['network']
    pool_address = token['pool_address']
    price_at_call = token['price_at_call']
    current_ath = token.get('ath_price', 0)
    current_ath_roi = token.get('ath_roi_percent', 0)
    
    print(f"\n[{idx}/{len(all_tokens)}] Processing {ticker} on {network}")
    print(f"  Current ATH: ${current_ath:.8f} ({current_ath_roi:.2f}% ROI)")
    
    # Map network names for GeckoTerminal
    network_map = {
        'ethereum': 'eth',
        'solana': 'solana',
        'bsc': 'bsc',
        'polygon': 'polygon',
        'arbitrum': 'arbitrum',
        'base': 'base'
    }
    
    gecko_network = network_map.get(network, network)
    
    # Fetch OHLCV data from GeckoTerminal
    url = f"https://api.geckoterminal.com/api/v2/networks/{gecko_network}/pools/{pool_address}/ohlcv/day"
    params = {
        "aggregate": 1,
        "limit": 1000,
        "currency": "usd"
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code != 200:
            print(f"  ⚠️ API error: {response.status_code}")
            error_count += 1
            continue
        
        data = response.json()
        ohlcv_list = data.get("data", {}).get("attributes", {}).get("ohlcv_list", [])
        
        if not ohlcv_list:
            print(f"  ⚠️ No OHLCV data available")
            skipped_count += 1
            continue
        
        # Parse call timestamp
        call_timestamp = token.get('buy_timestamp') or token.get('created_at')
        call_str = call_timestamp.replace("+00:00", "").split(".")[0]
        call_dt = datetime.strptime(call_str, "%Y-%m-%dT%H:%M:%S")
        call_unix = int(call_dt.timestamp())
        
        # Find ATH after call
        max_high = 0
        max_timestamp = None
        
        for candle in ohlcv_list:
            timestamp, open_price, high, low, close, volume = candle
            
            if timestamp >= call_unix and high > max_high:
                max_high = high
                max_timestamp = timestamp
        
        if max_high > 0:
            calculated_roi = ((max_high - price_at_call) / price_at_call) * 100
            
            # Check if recalculated ATH is different
            if abs(max_high - current_ath) > 0.00000001:  # Small tolerance for float comparison
                print(f"  📊 Calculated ATH: ${max_high:.8f} ({calculated_roi:.2f}% ROI)")
                
                if max_high > current_ath:
                    print(f"  ⚠️ HIGHER ATH FOUND! Difference: ${max_high - current_ath:.8f}")
                    
                    # Update the database
                    update_url = f"{SUPABASE_URL}/rest/v1/crypto_calls?id=eq.{token['id']}"
                    update_data = {
                        "ath_price": max_high,
                        "ath_roi_percent": calculated_roi,
                        "ath_timestamp": datetime.fromtimestamp(max_timestamp).isoformat() + "Z"
                    }
                    
                    update_response = requests.patch(
                        update_url,
                        headers=headers,
                        json=update_data
                    )
                    
                    if update_response.status_code in [200, 204]:
                        print(f"  ✅ Updated successfully!")
                        updated_count += 1
                    else:
                        print(f"  ❌ Update failed: {update_response.status_code}")
                        error_count += 1
                else:
                    print(f"  ℹ️ Current ATH is higher, keeping existing value")
                    skipped_count += 1
            else:
                print(f"  ✓ ATH matches, no update needed")
                skipped_count += 1
        else:
            print(f"  ⚠️ No valid price data after call")
            skipped_count += 1
            
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        error_count += 1
    
    # Rate limiting - GeckoTerminal allows 30 req/min
    time.sleep(2)  # 2 seconds between requests = 30 req/min
    
    # Progress update every 10 tokens
    if idx % 10 == 0:
        print("\n" + "=" * 60)
        print(f"Progress: {idx}/{len(all_tokens)} tokens processed")
        print(f"Updated: {updated_count}, Skipped: {skipped_count}, Errors: {error_count}")
        print("=" * 60)

print("\n" + "=" * 60)
print("FINAL SUMMARY")
print("=" * 60)
print(f"Total tokens processed: {len(all_tokens)}")
print(f"✅ Updated: {updated_count}")
print(f"⏭️ Skipped: {skipped_count}")
print(f"❌ Errors: {error_count}")
print("\nScript completed!")