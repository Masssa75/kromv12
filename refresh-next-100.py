import os
from supabase import create_client
from dotenv import load_dotenv
import requests
import time
from datetime import datetime, timedelta
import random

load_dotenv()
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

print("=== BATCH PRICE REFRESH (Tokens 201-300) ===")
print("Processing the next 100 tokens...\n")

# Get tokens 201-300
tokens = supabase.table('crypto_calls').select(
    'krom_id, ticker, contract_address, network, price_at_call'
).not_.is_('current_price', 'null').not_.is_('contract_address', 'null').order('price_updated_at', desc=False).range(200, 299).execute()

print(f"Processing {len(tokens.data)} tokens in batches of 30...\n")

updated = 0
failed = 0
updated_via_dex = 0
updated_via_gecko = 0

# Store all updated tokens for random sampling
all_updated_tokens = []

# Process in batches of 30
for i in range(0, len(tokens.data), 30):
    batch = tokens.data[i:i+30]
    batch_num = i//30 + 1
    print(f"\nBatch {batch_num}: Processing {len(batch)} tokens...")
    
    # Track which tokens we're looking for
    tokens_by_address = {}
    for token in batch:
        tokens_by_address[token['contract_address'].lower()] = token
    
    # Prepare addresses for DexScreener
    addresses = ','.join([t['contract_address'] for t in batch])
    
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
                            roi_str = f" (ROI: {roi:.1f}%)"
                        else:
                            roi_str = ""
                            roi = None
                        
                        result = supabase.table('crypto_calls').update(update_data).eq('krom_id', token['krom_id']).execute()
                        
                        if result.data:
                            updated += 1
                            updated_via_dex += 1
                            print(f"  ✅ {token['ticker']}: ${new_price:.10f}{roi_str} [DexScreener]")
                            all_updated_tokens.append({
                                'ticker': token['ticker'],
                                'price': new_price,
                                'roi': roi,
                                'source': 'DexScreener'
                            })
    except Exception as e:
        print(f"  ❌ DexScreener error: {e}")
    
    # Now try GeckoTerminal for ALL tokens not found in DexScreener
    missing_tokens = []
    for address, token in tokens_by_address.items():
        if address not in found_in_dexscreener:
            missing_tokens.append(token)
    
    if missing_tokens:
        print(f"  🔄 Trying GeckoTerminal for {len(missing_tokens)} tokens not on DexScreener...")
        
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
                                    roi_str = f" (ROI: {roi:.1f}%)"
                                else:
                                    roi_str = ""
                                    roi = None
                                
                                result = supabase.table('crypto_calls').update(update_data).eq('krom_id', token['krom_id']).execute()
                                
                                if result.data:
                                    updated += 1
                                    updated_via_gecko += 1
                                    liquidity = float(best_pool['attributes'].get('reserve_in_usd', 0))
                                    print(f"  ✅ {token['ticker']}: ${best_price:.10f}{roi_str} [GeckoTerminal, liq: ${liquidity:,.0f}]")
                                    all_updated_tokens.append({
                                        'ticker': token['ticker'],
                                        'price': best_price,
                                        'roi': roi,
                                        'source': 'GeckoTerminal'
                                    })
                                else:
                                    failed += 1
                                    print(f"  ❌ {token['ticker']}: Database update failed")
                            else:
                                failed += 1
                                print(f"  ❌ {token['ticker']}: GeckoTerminal returned 0 price")
                        else:
                            failed += 1
                            print(f"  ❌ {token['ticker']}: No pools found on GeckoTerminal")
                    else:
                        failed += 1
                        print(f"  ❌ {token['ticker']}: GeckoTerminal error {gecko_response.status_code}")
                except Exception as e:
                    failed += 1
                    print(f"  ❌ {token['ticker']}: Error - {str(e)[:50]}")
            else:
                failed += 1
                print(f"  ❌ {token['ticker']}: No network specified")
    
    print(f"\n  Batch summary: {len(found_in_dexscreener)} from DexScreener, {len(missing_tokens)} tried on GeckoTerminal")
    time.sleep(0.5)  # Small delay between batches

print(f"\n\n=== FINAL SUMMARY ===")
print(f"Total processed: {updated + failed}")
print(f"Successfully updated: {updated} tokens")
print(f"  - Via DexScreener: {updated_via_dex}")
print(f"  - Via GeckoTerminal: {updated_via_gecko}")
print(f"Failed/Dead tokens: {failed}")
print(f"Success rate: {updated/(updated+failed)*100:.1f}%" if updated + failed > 0 else "N/A")

# Show remaining count
remaining = supabase.table('crypto_calls').select('id', count='exact').not_.is_('current_price', 'null').not_.is_('contract_address', 'null').lt('price_updated_at', datetime.utcnow() - timedelta(hours=2)).execute()
print(f"\nRemaining tokens to update: {remaining.count}")

# Show 5 random samples
if all_updated_tokens:
    print(f"\n\n=== 5 RANDOM TOKENS TO SPOT CHECK ===\n")
    for token in random.sample(all_updated_tokens, min(5, len(all_updated_tokens))):
        print(f"{token['ticker']}:")
        print(f"  Price: ${token['price']:.10f}")
        if token['roi'] is not None:
            print(f"  ROI: {token['roi']:.1f}%")
        else:
            print(f"  ROI: N/A")
        print(f"  Source: {token['source']}")
        print()