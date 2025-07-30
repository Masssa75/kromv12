import os
from supabase import create_client
from dotenv import load_dotenv
import requests
import time
from datetime import datetime, timedelta

load_dotenv()
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

print("=== REFRESH ALL REMAINING PRICES ===")
print(f"Starting at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("This will process all remaining tokens with the proven logic\n")

# Get count of tokens to update
count_result = supabase.table('crypto_calls').select('id', count='exact').not_.is_('current_price', 'null').not_.is_('contract_address', 'null').lt('price_updated_at', datetime.utcnow() - timedelta(hours=2)).execute()
total_to_update = count_result.count

print(f"Found {total_to_update} tokens needing updates")
print("Processing in batches of 30...\n")

updated = 0
failed = 0
updated_via_dex = 0
updated_via_gecko = 0
start_time = time.time()

# Process all remaining tokens starting from offset 400
offset = 400  # We've already done 0-399

while offset < total_to_update + 400:  # Add 400 since we started at offset 400
    # Get next batch of 30 tokens
    tokens = supabase.table('crypto_calls').select(
        'krom_id, ticker, contract_address, network, price_at_call'
    ).not_.is_('current_price', 'null').not_.is_('contract_address', 'null').order('price_updated_at', desc=False).range(offset, offset + 29).execute()
    
    if not tokens.data:
        break
    
    batch_num = (offset - 400) // 30 + 1
    print(f"\nBatch {batch_num} (tokens {offset+1}-{offset+len(tokens.data)}): Processing {len(tokens.data)} tokens...")
    
    # Track which tokens we're looking for
    tokens_by_address = {}
    for token in tokens.data:
        tokens_by_address[token['contract_address'].lower()] = token
    
    # Prepare addresses for DexScreener
    addresses = ','.join([t['contract_address'] for t in tokens.data])
    
    # Track which tokens were found
    found_in_dexscreener = set()
    
    try:
        # Call DexScreener batch API
        response = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{addresses}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Process DexScreener results
            if data.get('pairs'):
                for pair in data['pairs']:
                    contract = pair['baseToken']['address'].lower()
                    if contract in tokens_by_address and contract not in found_in_dexscreener:
                        found_in_dexscreener.add(contract)
                        token = tokens_by_address[contract]
                        new_price = float(pair['priceUsd'])
                        
                        # Update database
                        update_data = {
                            'current_price': new_price,
                            'price_updated_at': datetime.utcnow().isoformat()
                        }
                        
                        if token['price_at_call'] and token['price_at_call'] > 0:
                            roi = ((new_price - token['price_at_call']) / token['price_at_call']) * 100
                            update_data['roi_percent'] = roi
                        
                        result = supabase.table('crypto_calls').update(update_data).eq('krom_id', token['krom_id']).execute()
                        
                        if result.data:
                            updated += 1
                            updated_via_dex += 1
    except Exception as e:
        print(f"  ⚠️ DexScreener error: {str(e)[:100]}")
    
    # Now try GeckoTerminal for ALL tokens not found in DexScreener
    missing_tokens = []
    for address, token in tokens_by_address.items():
        if address not in found_in_dexscreener:
            missing_tokens.append(token)
    
    if missing_tokens:
        for token in missing_tokens:
            if token['network']:
                network_map = {'ethereum': 'eth', 'solana': 'solana', 'bsc': 'bsc', 'polygon': 'polygon', 'arbitrum': 'arbitrum', 'base': 'base'}
                api_network = network_map.get(token['network'], token['network'])
                
                time.sleep(0.3)  # Rate limit for GeckoTerminal
                
                try:
                    gecko_response = requests.get(
                        f"https://api.geckoterminal.com/api/v2/networks/{api_network}/tokens/{token['contract_address']}/pools"
                    )
                    
                    if gecko_response.status_code == 200:
                        gecko_data = gecko_response.json()
                        pools = gecko_data.get('data', [])
                        
                        if pools:
                            # Sort by liquidity (FIXED logic)
                            sorted_pools = sorted(pools, key=lambda p: float(p['attributes'].get('reserve_in_usd', 0)), reverse=True)
                            best_pool = sorted_pools[0]
                            best_price = float(best_pool['attributes'].get('token_price_usd', 0))
                            
                            if best_price > 0:
                                # Update database
                                update_data = {
                                    'current_price': best_price,
                                    'price_updated_at': datetime.utcnow().isoformat()
                                }
                                
                                if token['price_at_call'] and token['price_at_call'] > 0:
                                    roi = ((best_price - token['price_at_call']) / token['price_at_call']) * 100
                                    update_data['roi_percent'] = roi
                                
                                result = supabase.table('crypto_calls').update(update_data).eq('krom_id', token['krom_id']).execute()
                                
                                if result.data:
                                    updated += 1
                                    updated_via_gecko += 1
                            else:
                                failed += 1
                        else:
                            failed += 1
                    elif gecko_response.status_code == 429:
                        print(f"  ⚠️ GeckoTerminal rate limit hit, waiting 60s...")
                        time.sleep(60)  # Wait longer on rate limit
                        failed += 1
                    else:
                        failed += 1
                except Exception as e:
                    failed += 1
            else:
                failed += 1
    
    # Progress update
    print(f"  Batch complete: {len(found_in_dexscreener)} via DexScreener, {len(missing_tokens)-failed} via GeckoTerminal")
    print(f"  Total progress: {updated}/{offset-400+len(tokens.data)} tokens ({updated/(offset-400+len(tokens.data))*100:.1f}%)")
    
    # Rate limiting and progress tracking
    if batch_num % 10 == 0:
        elapsed = time.time() - start_time
        rate = updated / elapsed * 60
        eta_minutes = (total_to_update - (updated + failed)) / rate if rate > 0 else 0
        print(f"\n  === Progress Report ===")
        print(f"  Updated: {updated} | Failed: {failed}")
        print(f"  Rate: {rate:.1f} tokens/minute")
        print(f"  ETA: {eta_minutes:.1f} minutes")
        print(f"  Pausing 5 seconds...")
        time.sleep(5)
    
    offset += 30
    time.sleep(0.5)  # Small delay between batches

# Final summary
elapsed_total = time.time() - start_time
print(f"\n\n=== FINAL SUMMARY ===")
print(f"Completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Total time: {elapsed_total/60:.1f} minutes")
print(f"Total processed: {updated + failed}")
print(f"Successfully updated: {updated} tokens")
print(f"  - Via DexScreener: {updated_via_dex}")
print(f"  - Via GeckoTerminal: {updated_via_gecko}")
print(f"Failed/Dead tokens: {failed}")
print(f"Success rate: {updated/(updated+failed)*100:.1f}%" if updated + failed > 0 else "N/A")
print(f"Average rate: {updated/elapsed_total*60:.1f} tokens/minute")

# Final check
remaining = supabase.table('crypto_calls').select('id', count='exact').not_.is_('current_price', 'null').not_.is_('contract_address', 'null').lt('price_updated_at', datetime.utcnow() - timedelta(hours=2)).execute()
print(f"\nRemaining tokens to update: {remaining.count}")