#!/usr/bin/env python3
import json
import urllib.request
import urllib.parse
import time
from datetime import datetime

print("=== Historical Price Population - Batch Processor ===")
print(f"Started: {datetime.now()}")
print()

# Configuration
BATCH_SIZE = 50
RATE_LIMIT_DELAY = 0.5  # seconds between API calls

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

# Network mapping
def map_network(network):
    mapping = {
        'ethereum': 'eth',
        'solana': 'solana',
        'bsc': 'bsc',
        'polygon': 'polygon',
        'arbitrum': 'arbitrum',
        'base': 'base',
        'abstract': 'abstract'
    }
    return mapping.get(network.lower(), network.lower())

# Process batch of tokens
def process_batch(batch_number, offset):
    print(f"\n{'='*60}")
    print(f"BATCH {batch_number} - Processing tokens {offset+1} to {offset+BATCH_SIZE}")
    print(f"{'='*60}")
    
    # Get tokens without historical price, ordered by age
    query_url = f"{supabase_url}?select=krom_id,ticker,network,pool_address,contract_address,buy_timestamp,raw_data,historical_price_usd,price_source&historical_price_usd=is.null&order=buy_timestamp.asc&limit={BATCH_SIZE}&offset={offset}"
    
    req = urllib.request.Request(query_url)
    req.add_header('apikey', service_key)
    req.add_header('Authorization', f'Bearer {service_key}')
    
    try:
        response = urllib.request.urlopen(req)
        tokens = json.loads(response.read().decode())
        
        if not tokens:
            print("No more tokens to process!")
            return 0, 0, 0
        
        print(f"Found {len(tokens)} tokens to process")
        
        success_count = 0
        krom_price_count = 0
        failed_count = 0
        
        for i, token in enumerate(tokens):
            ticker = token.get('ticker', 'Unknown')
            network = token.get('network', 'unknown')
            pool = token.get('pool_address')
            contract = token.get('contract_address', 'unknown')
            buy_timestamp = token.get('buy_timestamp')
            raw_data = token.get('raw_data', {})
            krom_id = token.get('krom_id')
            
            print(f"\n{i+1}. {ticker} ({network}) - {buy_timestamp[:10] if buy_timestamp else 'No date'}")
            
            # First check if we have KROM price
            krom_price = None
            try:
                krom_price = float(raw_data.get('trade', {}).get('buyPrice', 0))
                if krom_price > 0:
                    print(f"   ✅ KROM price available: ${krom_price:.8f}")
                    
                    # Update database with KROM price
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
                    
                    try:
                        urllib.request.urlopen(update_req)
                        print(f"   ✅ Updated with KROM price")
                        krom_price_count += 1
                        continue
                    except Exception as e:
                        print(f"   ❌ Failed to update: {e}")
            except:
                pass
            
            # If no KROM price, try to fetch from GeckoTerminal
            if not pool or not buy_timestamp:
                print(f"   ❌ Missing pool or timestamp - skipping")
                failed_count += 1
                continue
            
            # Convert timestamp
            unix_timestamp = int(datetime.fromisoformat(buy_timestamp.replace('Z', '+00:00')).timestamp())
            
            # Try with original network first
            request_data = {
                "contractAddress": contract,
                "network": network,
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
            
            fetched_price = None
            price_source = None
            
            try:
                edge_response = urllib.request.urlopen(edge_req)
                edge_data = json.loads(edge_response.read().decode())
                
                if edge_data.get('price'):
                    fetched_price = float(edge_data['price'])
                    price_source = 'GECKO'
                    print(f"   ✅ Fetched price: ${fetched_price:.8f}")
            except urllib.error.HTTPError as e:
                if e.code == 400 and network.lower() == 'ethereum':
                    # Try with network mapping
                    print(f"   🔄 Trying with network mapping: ethereum -> eth")
                    request_data['network'] = 'eth'
                    
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
                            price_source = 'GECKO'
                            print(f"   ✅ Fetched with mapping: ${fetched_price:.8f}")
                    except:
                        pass
            
            # Update database if we got a price
            if fetched_price is not None:
                update_data = {
                    'historical_price_usd': fetched_price,
                    'price_source': price_source,
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
                
                try:
                    urllib.request.urlopen(update_req)
                    print(f"   ✅ Updated database")
                    success_count += 1
                except Exception as e:
                    print(f"   ❌ Failed to update: {e}")
                    failed_count += 1
            else:
                # Mark as dead token
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
                
                try:
                    urllib.request.urlopen(update_req)
                    print(f"   💀 Marked as DEAD_TOKEN")
                    failed_count += 1
                except Exception as e:
                    print(f"   ❌ Failed to update: {e}")
            
            # Rate limiting
            time.sleep(RATE_LIMIT_DELAY)
        
        print(f"\n📊 Batch {batch_number} Summary:")
        print(f"   KROM prices used: {krom_price_count}")
        print(f"   GeckoTerminal prices fetched: {success_count}")
        print(f"   Failed/Dead tokens: {failed_count}")
        print(f"   Total processed: {len(tokens)}")
        
        return len(tokens), krom_price_count + success_count, failed_count
        
    except Exception as e:
        print(f"❌ Error processing batch: {e}")
        return 0, 0, 0

# Main processing loop
print("\n🚀 Starting batch processing...")
print(f"Batch size: {BATCH_SIZE} tokens")
print(f"Rate limit: {RATE_LIMIT_DELAY}s between calls")

batch_number = 1
offset = 0
total_processed = 0
total_success = 0
total_failed = 0

while True:
    processed, success, failed = process_batch(batch_number, offset)
    
    if processed == 0:
        break
    
    total_processed += processed
    total_success += success
    total_failed += failed
    
    batch_number += 1
    offset += BATCH_SIZE
    
    # Show running totals
    print(f"\n📈 Running Totals:")
    print(f"   Total processed: {total_processed}")
    print(f"   Total with prices: {total_success}")
    print(f"   Total failed/dead: {total_failed}")
    
    # Ask to continue after each batch
    if processed == BATCH_SIZE:
        print(f"\n🤔 Continue to batch {batch_number}? (y/N): ", end='', flush=True)
        try:
            # Auto-continue for now
            print("y (auto-continuing)")
            continue
        except:
            break
    else:
        print(f"\n✅ Completed! No more tokens to process.")
        break

print(f"\n{'='*60}")
print(f"FINAL SUMMARY")
print(f"{'='*60}")
print(f"Total tokens processed: {total_processed}")
print(f"Successfully priced: {total_success} ({(total_success/total_processed*100):.1f}%)")
print(f"Failed/Dead tokens: {total_failed} ({(total_failed/total_processed*100):.1f}%)")
print(f"Completed: {datetime.now()}")