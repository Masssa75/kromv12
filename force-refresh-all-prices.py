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

print("=== FORCE REFRESH ALL PRICES ===")
print("This will update all tokens that haven't been refreshed in 2+ hours\n")

# Get tokens not updated in last 2 hours
two_hours_ago = (datetime.utcnow() - timedelta(hours=2)).isoformat()

# First get count
count_result = supabase.table('crypto_calls').select('id', count='exact').not_.is_('current_price', 'null').not_.is_('contract_address', 'null').lt('price_updated_at', two_hours_ago).execute()
total_to_update = count_result.count

print(f"Found {total_to_update} tokens needing refresh")
print("Processing in batches of 30 (DexScreener batch limit)...\n")

updated = 0
failed = 0
batch_num = 0

# Process in batches
while updated + failed < total_to_update:
    batch_num += 1
    
    # Get next batch
    tokens = supabase.table('crypto_calls').select(
        'krom_id, ticker, contract_address, network, price_at_call'
    ).not_.is_('current_price', 'null').not_.is_('contract_address', 'null').lt('price_updated_at', two_hours_ago).limit(30).execute()
    
    if not tokens.data:
        break
    
    print(f"\nBatch {batch_num}: Processing {len(tokens.data)} tokens...")
    
    # Prepare addresses for batch API call
    addresses = ','.join([t['contract_address'] for t in tokens.data])
    
    try:
        # Call DexScreener batch API
        response = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{addresses}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Process results
            found_prices = {}
            if data.get('pairs'):
                for pair in data['pairs']:
                    contract = pair['baseToken']['address'].lower()
                    if contract not in found_prices:
                        found_prices[contract] = float(pair['priceUsd'])
            
            # Update database for found prices
            for token in tokens.data:
                contract_lower = token['contract_address'].lower()
                
                if contract_lower in found_prices:
                    new_price = found_prices[contract_lower]
                    
                    # Calculate ROI
                    update_data = {
                        'current_price': new_price,
                        'price_updated_at': datetime.utcnow().isoformat()
                    }
                    
                    if token['price_at_call'] and token['price_at_call'] > 0:
                        roi = ((new_price - token['price_at_call']) / token['price_at_call']) * 100
                        update_data['roi_percent'] = roi
                    
                    # Update
                    result = supabase.table('crypto_calls').update(update_data).eq('krom_id', token['krom_id']).execute()
                    
                    if result.data:
                        updated += 1
                        print(f"  ✅ {token['ticker']}: ${new_price:.10f}")
                else:
                    # Try GeckoTerminal for missing ones
                    if token['network']:
                        network_map = {'ethereum': 'eth', 'solana': 'solana', 'bsc': 'bsc', 'polygon': 'polygon'}
                        api_network = network_map.get(token['network'], token['network'])
                        
                        time.sleep(0.3)  # Rate limit
                        gecko_response = requests.get(
                            f"https://api.geckoterminal.com/api/v2/networks/{api_network}/tokens/{token['contract_address']}/pools"
                        )
                        
                        if gecko_response.status_code == 200:
                            gecko_data = gecko_response.json()
                            pools = gecko_data.get('data', [])
                            
                            if pools:
                                # NEW LOGIC: Sort by liquidity
                                sorted_pools = sorted(pools, key=lambda p: float(p['attributes'].get('reserve_in_usd', 0)), reverse=True)
                                best_price = float(sorted_pools[0]['attributes'].get('token_price_usd', 0))
                                
                                if best_price > 0:
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
                                        print(f"  ✅ {token['ticker']}: ${best_price:.10f} (via GeckoTerminal)")
                                else:
                                    failed += 1
                                    print(f"  ❌ {token['ticker']}: No valid price found")
                            else:
                                failed += 1
                                print(f"  ❌ {token['ticker']}: No pools on GeckoTerminal")
                        else:
                            failed += 1
                            print(f"  ❌ {token['ticker']}: GeckoTerminal error {gecko_response.status_code}")
                    else:
                        failed += 1
                        print(f"  ❌ {token['ticker']}: No network specified")
        else:
            print(f"  ❌ DexScreener API error: {response.status_code}")
            failed += len(tokens.data)
            
    except Exception as e:
        print(f"  ❌ Error: {e}")
        failed += len(tokens.data)
    
    print(f"\nProgress: {updated + failed}/{total_to_update} ({(updated + failed)/total_to_update*100:.1f}%)")
    print(f"Updated: {updated}, Failed: {failed}")
    
    if batch_num % 10 == 0:
        print("\nPausing for 5 seconds to avoid rate limits...")
        time.sleep(5)

print(f"\n\n=== FINAL SUMMARY ===")
print(f"Total processed: {updated + failed}")
print(f"Successfully updated: {updated}")
print(f"Failed/Dead tokens: {failed}")
print(f"Success rate: {updated/(updated+failed)*100:.1f}%" if updated + failed > 0 else "N/A")