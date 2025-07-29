#!/usr/bin/env python3
import json
import urllib.request
import urllib.parse
import time
from datetime import datetime

print("=== Smart Historical Price Population ===")
print(f"Started: {datetime.now()}")
print()

# Configuration
BATCH_SIZE = 50
RATE_LIMIT_DELAY = 0.3  # seconds between API calls

# Get service key
service_key = None
try:
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('SUPABASE_SERVICE_ROLE_KEY='):
                service_key = line.split('=', 1)[1].strip()
                break
except:
    print("❌ Could not read .env file")
    exit(1)

supabase_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/rest/v1/crypto_calls"
edge_function_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-historical"

print("📊 Strategy:")
print("1. Use KROM price if available (most accurate)")
print("2. Fetch from GeckoTerminal if timestamp exists")
print("3. Mark as NO_TIMESTAMP if missing timestamp")
print()

# First, let's see what we're working with
def get_status():
    # Count tokens needing prices
    query_url = f"{supabase_url}?select=count&historical_price_usd=is.null"
    req = urllib.request.Request(query_url)
    req.add_header('apikey', service_key)
    req.add_header('Authorization', f'Bearer {service_key}')
    req.add_header('Prefer', 'count=exact')
    
    try:
        response = urllib.request.urlopen(req)
        total_without_price = int(response.headers.get('content-range', '0-0/0').split('/')[-1])
        
        # Count those with timestamps
        query_url = f"{supabase_url}?select=count&historical_price_usd=is.null&buy_timestamp=not.is.null"
        req = urllib.request.Request(query_url)
        req.add_header('apikey', service_key)
        req.add_header('Authorization', f'Bearer {service_key}')
        req.add_header('Prefer', 'count=exact')
        
        response = urllib.request.urlopen(req)
        with_timestamp = int(response.headers.get('content-range', '0-0/0').split('/')[-1])
        
        # Count those with KROM prices
        query_url = f"{supabase_url}?select=count&historical_price_usd=is.null&raw_data->>trade.buyPrice=not.is.null"
        req = urllib.request.Request(query_url)
        req.add_header('apikey', service_key)
        req.add_header('Authorization', f'Bearer {service_key}')
        req.add_header('Prefer', 'count=exact')
        
        response = urllib.request.urlopen(req)
        with_krom_price = int(response.headers.get('content-range', '0-0/0').split('/')[-1])
        
        print(f"📈 Current Status:")
        print(f"   Total without price: {total_without_price}")
        print(f"   - With KROM price available: ~{with_krom_price}")
        print(f"   - With timestamp (can fetch): {with_timestamp}")
        print(f"   - No timestamp (can't fetch): ~{total_without_price - with_timestamp}")
        print()
        
        return total_without_price, with_timestamp, with_krom_price
        
    except Exception as e:
        print(f"❌ Error getting status: {e}")
        return 0, 0, 0

# Get initial status
total_without_price, with_timestamp, with_krom_price = get_status()

# Process batch
def process_batch(batch_number, focus_on_timestamp=True):
    print(f"\n{'='*60}")
    print(f"BATCH {batch_number}")
    print(f"{'='*60}")
    
    # Query strategy - prioritize tokens with timestamps
    if focus_on_timestamp:
        # Get tokens WITH timestamps first
        query_url = f"{supabase_url}?select=krom_id,ticker,network,pool_address,contract_address,buy_timestamp,raw_data&historical_price_usd=is.null&buy_timestamp=not.is.null&order=buy_timestamp.asc&limit={BATCH_SIZE}"
    else:
        # Then get any remaining tokens
        query_url = f"{supabase_url}?select=krom_id,ticker,network,pool_address,contract_address,buy_timestamp,raw_data&historical_price_usd=is.null&order=created_at.asc&limit={BATCH_SIZE}"
    
    req = urllib.request.Request(query_url)
    req.add_header('apikey', service_key)
    req.add_header('Authorization', f'Bearer {service_key}')
    
    try:
        response = urllib.request.urlopen(req)
        tokens = json.loads(response.read().decode())
        
        if not tokens:
            return 0, 0, 0, 0
        
        print(f"Processing {len(tokens)} tokens...")
        
        krom_count = 0
        gecko_count = 0
        no_timestamp_count = 0
        dead_count = 0
        
        for i, token in enumerate(tokens):
            ticker = token.get('ticker', 'Unknown')
            network = token.get('network', 'unknown')
            pool = token.get('pool_address')
            contract = token.get('contract_address', 'unknown')
            buy_timestamp = token.get('buy_timestamp')
            raw_data = token.get('raw_data', {})
            krom_id = token.get('krom_id')
            
            # First check for KROM price
            krom_price = None
            try:
                krom_price = float(raw_data.get('trade', {}).get('buyPrice', 0))
                if krom_price > 0:
                    # Update with KROM price
                    update_data = {
                        'historical_price_usd': krom_price,
                        'price_source': 'KROM',
                        'price_updated_at': datetime.now().isoformat()
                    }
                    
                    update_url = f"{supabase_url}?krom_id=eq.{krom_id}"
                    update_req = urllib.request.Request(
                        update_url,
                        data=json.dumps(update_data).encode('utf-8'),
                        headers={
                            'apikey': service_key,
                            'Authorization': f'Bearer {service_key}',
                            'Content-Type': 'application/json',
                            'Prefer': 'return=minimal'
                        },
                        method='PATCH'
                    )
                    
                    urllib.request.urlopen(update_req)
                    print(f"{i+1}. {ticker}: ✅ KROM ${krom_price:.8f}")
                    krom_count += 1
                    continue
            except:
                pass
            
            # No KROM price - check if we can fetch from Gecko
            if not buy_timestamp:
                # No timestamp - can't fetch historical
                update_data = {
                    'price_source': 'NO_TIMESTAMP',
                    'price_updated_at': datetime.now().isoformat()
                }
                
                update_url = f"{supabase_url}?krom_id=eq.{krom_id}"
                update_req = urllib.request.Request(
                    update_url,
                    data=json.dumps(update_data).encode('utf-8'),
                    headers={
                        'apikey': service_key,
                        'Authorization': f'Bearer {service_key}',
                        'Content-Type': 'application/json',
                        'Prefer': 'return=minimal'
                    },
                    method='PATCH'
                )
                
                urllib.request.urlopen(update_req)
                print(f"{i+1}. {ticker}: ⏰ No timestamp")
                no_timestamp_count += 1
                continue
            
            if not pool:
                # No pool address - can't fetch
                update_data = {
                    'price_source': 'NO_POOL',
                    'price_updated_at': datetime.now().isoformat()
                }
                
                update_url = f"{supabase_url}?krom_id=eq.{krom_id}"
                update_req = urllib.request.Request(
                    update_url,
                    data=json.dumps(update_data).encode('utf-8'),
                    headers={
                        'apikey': service_key,
                        'Authorization': f'Bearer {service_key}',
                        'Content-Type': 'application/json',
                        'Prefer': 'return=minimal'
                    },
                    method='PATCH'
                )
                
                urllib.request.urlopen(update_req)
                print(f"{i+1}. {ticker}: ❌ No pool")
                dead_count += 1
                continue
            
            # Try to fetch from GeckoTerminal
            unix_timestamp = int(datetime.fromisoformat(buy_timestamp.replace('Z', '+00:00')).timestamp())
            
            # Map network if needed
            mapped_network = network
            if network.lower() == 'ethereum':
                mapped_network = 'eth'
            
            request_data = {
                "contractAddress": contract,
                "network": mapped_network,
                "poolAddress": pool,
                "timestamp": unix_timestamp
            }
            
            edge_req = urllib.request.Request(
                edge_function_url,
                data=json.dumps(request_data).encode('utf-8'),
                headers={
                    'Authorization': f'Bearer {service_key}',
                    'Content-Type': 'application/json'
                },
                method='POST'
            )
            
            try:
                edge_response = urllib.request.urlopen(edge_req)
                edge_data = json.loads(edge_response.read().decode())
                
                if edge_data.get('price'):
                    fetched_price = float(edge_data['price'])
                    
                    update_data = {
                        'historical_price_usd': fetched_price,
                        'price_source': 'GECKO',
                        'price_updated_at': datetime.now().isoformat()
                    }
                    
                    update_url = f"{supabase_url}?krom_id=eq.{krom_id}"
                    update_req = urllib.request.Request(
                        update_url,
                        data=json.dumps(update_data).encode('utf-8'),
                        headers={
                            'apikey': service_key,
                            'Authorization': f'Bearer {service_key}',
                            'Content-Type': 'application/json',
                            'Prefer': 'return=minimal'
                        },
                        method='PATCH'
                    )
                    
                    urllib.request.urlopen(update_req)
                    print(f"{i+1}. {ticker}: 🦎 Gecko ${fetched_price:.8f}")
                    gecko_count += 1
                else:
                    # No price found
                    update_data = {
                        'price_source': 'DEAD_TOKEN',
                        'price_updated_at': datetime.now().isoformat()
                    }
                    
                    update_url = f"{supabase_url}?krom_id=eq.{krom_id}"
                    update_req = urllib.request.Request(
                        update_url,
                        data=json.dumps(update_data).encode('utf-8'),
                        headers={
                            'apikey': service_key,
                            'Authorization': f'Bearer {service_key}',
                            'Content-Type': 'application/json',
                            'Prefer': 'return=minimal'
                        },
                        method='PATCH'
                    )
                    
                    urllib.request.urlopen(update_req)
                    print(f"{i+1}. {ticker}: 💀 Dead token")
                    dead_count += 1
                    
            except Exception as e:
                print(f"{i+1}. {ticker}: ❌ Error: {str(e)[:50]}")
                dead_count += 1
            
            # Rate limiting
            time.sleep(RATE_LIMIT_DELAY)
        
        print(f"\n📊 Batch Summary:")
        print(f"   KROM prices: {krom_count}")
        print(f"   Gecko prices: {gecko_count}")
        print(f"   No timestamp: {no_timestamp_count}")
        print(f"   Dead/Failed: {dead_count}")
        
        return len(tokens), krom_count, gecko_count, no_timestamp_count + dead_count
        
    except Exception as e:
        print(f"❌ Error processing batch: {e}")
        return 0, 0, 0, 0

# Main processing
batch_number = 1
total_processed = 0
total_krom = 0
total_gecko = 0
total_failed = 0

# First process all tokens WITH timestamps
print("🎯 Phase 1: Processing tokens WITH timestamps...")
while True:
    processed, krom, gecko, failed = process_batch(batch_number, focus_on_timestamp=True)
    
    if processed == 0:
        print("\n✅ Phase 1 complete - all tokens with timestamps processed!")
        break
    
    total_processed += processed
    total_krom += krom
    total_gecko += gecko
    total_failed += failed
    
    batch_number += 1
    
    if batch_number > 5:  # Limit for testing
        print("\n⏸️  Stopping after 5 batches for testing")
        break

print(f"\n{'='*60}")
print(f"SUMMARY")
print(f"{'='*60}")
print(f"Total processed: {total_processed}")
print(f"KROM prices used: {total_krom}")
print(f"Gecko prices fetched: {total_gecko}")
print(f"Failed/No data: {total_failed}")
print(f"Success rate: {((total_krom + total_gecko) / total_processed * 100):.1f}%" if total_processed > 0 else "N/A")