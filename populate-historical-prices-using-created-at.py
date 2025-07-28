#!/usr/bin/env python3
import json
import urllib.request
import urllib.parse
import time
from datetime import datetime

print("=== Historical Price Population Using created_at Fallback ===")
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
print("2. Use buy_timestamp if available")
print("3. Use created_at as fallback timestamp")
print("4. Fetch from GeckoTerminal with appropriate timestamp")
print()

# Process batch
def process_batch(batch_number, offset):
    print(f"\n{'='*60}")
    print(f"BATCH {batch_number} - Processing tokens {offset+1} to {offset+BATCH_SIZE}")
    print(f"{'='*60}")
    
    # Get tokens without historical price, ordered by creation
    query_url = f"{supabase_url}?select=krom_id,ticker,network,pool_address,contract_address,buy_timestamp,created_at,raw_data&historical_price_usd=is.null&order=created_at.asc&limit={BATCH_SIZE}&offset={offset}"
    
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
        dead_count = 0
        
        for i, token in enumerate(tokens):
            ticker = token.get('ticker', 'Unknown')
            network = token.get('network', 'unknown')
            pool = token.get('pool_address')
            contract = token.get('contract_address', 'unknown')
            buy_timestamp = token.get('buy_timestamp')
            created_at = token.get('created_at')
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
            
            # No KROM price - need to fetch from Gecko
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
            
            # Determine which timestamp to use
            timestamp_to_use = buy_timestamp or created_at
            timestamp_source = "buy_timestamp" if buy_timestamp else "created_at"
            
            if not timestamp_to_use:
                print(f"{i+1}. {ticker}: ❌ No timestamp at all")
                dead_count += 1
                continue
            
            # Convert timestamp - handle various formats
            try:
                # Try parsing with Z suffix
                if 'Z' in timestamp_to_use:
                    unix_timestamp = int(datetime.fromisoformat(timestamp_to_use.replace('Z', '+00:00')).timestamp())
                elif '+' in timestamp_to_use:
                    # Already has timezone info
                    unix_timestamp = int(datetime.fromisoformat(timestamp_to_use).timestamp())
                else:
                    # No timezone info, assume UTC
                    unix_timestamp = int(datetime.fromisoformat(timestamp_to_use + '+00:00').timestamp())
            except:
                # Fallback parsing for non-standard formats
                # Remove microseconds if they're causing issues
                clean_timestamp = timestamp_to_use.split('.')[0] + '+00:00'
                unix_timestamp = int(datetime.fromisoformat(clean_timestamp).timestamp())
            
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
                        'price_source': f'GECKO_{timestamp_source.upper()}',
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
                    print(f"{i+1}. {ticker} ({network}): 🦎 ${fetched_price:.8f} using {timestamp_source}")
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
                    print(f"{i+1}. {ticker} ({network}): 💀 Dead token")
                    dead_count += 1
                    
            except urllib.error.HTTPError as e:
                error_body = e.read().decode() if e.code == 400 else str(e.code)
                print(f"{i+1}. {ticker} ({network}): ❌ HTTP {e.code} - {error_body[:50]}")
                
                # Mark as dead
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
                dead_count += 1
                
            except Exception as e:
                print(f"{i+1}. {ticker} ({network}): ❌ Error: {str(e)[:50]}")
                dead_count += 1
            
            # Rate limiting
            time.sleep(RATE_LIMIT_DELAY)
        
        print(f"\n📊 Batch Summary:")
        print(f"   KROM prices: {krom_count}")
        print(f"   Gecko prices: {gecko_count}")
        print(f"   Dead/Failed: {dead_count}")
        print(f"   Success rate: {((krom_count + gecko_count) / len(tokens) * 100):.1f}%")
        
        return len(tokens), krom_count, gecko_count, dead_count
        
    except Exception as e:
        print(f"❌ Error processing batch: {e}")
        return 0, 0, 0, 0

# Main processing
print("🚀 Starting batch processing with created_at fallback...")

batch_number = 1
offset = 0
total_processed = 0
total_krom = 0
total_gecko = 0
total_failed = 0

while batch_number <= 10:  # Process 10 batches = 500 tokens
    processed, krom, gecko, failed = process_batch(batch_number, offset)
    
    if processed == 0:
        print("\n✅ No more tokens to process!")
        break
    
    total_processed += processed
    total_krom += krom
    total_gecko += gecko
    total_failed += failed
    
    batch_number += 1
    offset += BATCH_SIZE
    
    # Show running totals
    print(f"\n📈 Running Totals:")
    print(f"   Total processed: {total_processed}")
    print(f"   KROM prices: {total_krom}")
    print(f"   Gecko prices: {total_gecko}")
    print(f"   Failed/Dead: {total_failed}")

print(f"\n{'='*60}")
print(f"FINAL SUMMARY")
print(f"{'='*60}")
print(f"Total tokens processed: {total_processed}")
if total_processed > 0:
    print(f"KROM prices used: {total_krom} ({(total_krom/total_processed*100):.1f}%)")
    print(f"Gecko prices fetched: {total_gecko} ({(total_gecko/total_processed*100):.1f}%)")
    print(f"Failed/Dead tokens: {total_failed} ({(total_failed/total_processed*100):.1f}%)")
    print(f"Overall success rate: {((total_krom + total_gecko) / total_processed * 100):.1f}%")
else:
    print("No tokens were processed.")
print(f"\nCompleted: {datetime.now()}")