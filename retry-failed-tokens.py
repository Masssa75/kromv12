import os
from supabase import create_client
from dotenv import load_dotenv
import requests
import time
from datetime import datetime

load_dotenv()
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

# List of failed tokens from previous run
failed_tickers = [
    'PUMP', 'SHADOW', 'CAP', 'RDP', 'AROS', 'JARVIS', 'POTUS', 'HONKTAILS', 
    'DATE', 'SUPERMAN TRUMP', 'DROOPY', 'BITO', 'ZEUS', 'THUMB', 'X PARTY', 
    'DOG', 'EYYREK', 'NOTEBOOK', 'JULES', 'BLEPE', 'DOGDRAGON', '⚡️', 
    'FROGETTE', 'MEDA', 'COCO', 'SPIKE', 'SHIBAKO', 'MOONCAT', 'DIARRHEA', 
    'DEXCOIN', 'APH', 'TEST', 'NOVAQ', 'SOLANA', 'LARRY', 'SPEECHLY'
]

print("=== RETRYING FAILED TOKENS WITH GECKOTERMINAL ===")
print(f"Attempting to update {len(set(failed_tickers))} unique failed tokens...\n")

updated = 0
still_failed = 0

# Get token data for failed tickers
for ticker in set(failed_tickers):  # Use set to avoid duplicates
    # Get token info from database
    result = supabase.table('crypto_calls').select(
        'krom_id, ticker, contract_address, network, price_at_call'
    ).eq('ticker', ticker).not_.is_('contract_address', 'null').limit(1).execute()
    
    if not result.data:
        print(f"❌ {ticker}: Not found in database")
        continue
        
    token = result.data[0]
    print(f"\nChecking {ticker}...")
    
    # Try DexScreener first (again, in case it's back online)
    try:
        response = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{token['contract_address']}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('pairs') and len(data['pairs']) > 0:
                new_price = float(data['pairs'][0]['priceUsd'])
                
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
                
                result = supabase.table('crypto_calls').update(update_data).eq('krom_id', token['krom_id']).execute()
                
                if result.data:
                    updated += 1
                    print(f"  ✅ Found on DexScreener: ${new_price:.10f}{roi_str}")
                    continue
    except:
        pass
    
    # Try GeckoTerminal as fallback
    if token['network']:
        network_map = {'ethereum': 'eth', 'solana': 'solana', 'bsc': 'bsc', 'polygon': 'polygon', 'arbitrum': 'arbitrum', 'base': 'base'}
        api_network = network_map.get(token['network'], token['network'])
        
        time.sleep(0.5)  # Rate limit
        try:
            gecko_response = requests.get(
                f"https://api.geckoterminal.com/api/v2/networks/{api_network}/tokens/{token['contract_address']}/pools"
            )
            
            if gecko_response.status_code == 200:
                gecko_data = gecko_response.json()
                pools = gecko_data.get('data', [])
                
                if pools:
                    # Use the FIXED logic: Sort by liquidity
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
                        
                        result = supabase.table('crypto_calls').update(update_data).eq('krom_id', token['krom_id']).execute()
                        
                        if result.data:
                            updated += 1
                            print(f"  ✅ Found on GeckoTerminal: ${best_price:.10f}{roi_str}")
                            print(f"     From pool: {best_pool['attributes'].get('name')} (liquidity: ${float(best_pool['attributes'].get('reserve_in_usd', 0)):,.0f})")
                        else:
                            still_failed += 1
                            print(f"  ❌ Database update failed")
                    else:
                        still_failed += 1
                        print(f"  ❌ GeckoTerminal returned 0 price")
                else:
                    still_failed += 1
                    print(f"  ❌ No pools on GeckoTerminal")
            else:
                still_failed += 1
                print(f"  ❌ GeckoTerminal API error: {gecko_response.status_code}")
        except Exception as e:
            still_failed += 1
            print(f"  ❌ Error: {e}")
    else:
        still_failed += 1
        print(f"  ❌ No network specified")

print(f"\n\n=== SUMMARY ===")
print(f"Successfully updated: {updated} tokens")
print(f"Still failed: {still_failed} tokens")
print(f"Recovery rate: {updated/(updated+still_failed)*100:.1f}%" if updated + still_failed > 0 else "N/A")