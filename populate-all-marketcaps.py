#!/usr/bin/env python3
"""
Comprehensive Market Cap Populator
===================================
1. Fetches supply data from DexScreener for all non-dead tokens
2. Populates market_cap_at_call (price_at_call × total_supply)
3. Populates ath_market_cap (ath_price × total_supply)
"""

import os
import time
import warnings
warnings.filterwarnings("ignore")
import requests
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Initialize Supabase
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

BATCH_SIZE = 30  # DexScreener can handle 30 tokens per API call

def fetch_supply_data_batch(contract_addresses):
    """Fetch supply data from DexScreener for multiple tokens"""
    addresses_param = ','.join(contract_addresses)
    url = f"https://api.dexscreener.com/latest/dex/tokens/{addresses_param}"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            
            # Map results by contract address
            results = {}
            for pair in data.get('pairs', []):
                addr = pair.get('baseToken', {}).get('address', '').lower()
                if addr and (addr not in results or 
                           float(pair.get('liquidity', {}).get('usd', 0) or 0) > 
                           float(results.get(addr, {}).get('liquidity', 0) or 0)):
                    
                    fdv = pair.get('fdv')
                    market_cap = pair.get('marketCap')
                    price = float(pair.get('priceUsd', 0))
                    
                    if fdv and price > 0:
                        results[addr] = {
                            'total_supply': fdv / price,
                            'circulating_supply': (market_cap / price) if market_cap and price > 0 else (fdv / price),
                            'fdv': fdv,
                            'market_cap': market_cap
                        }
            
            return results
    except Exception as e:
        print(f"Error fetching batch: {e}")
    
    return {}

def process_tokens():
    """Main processing function"""
    print("=" * 60)
    print("Market Cap Comprehensive Populator")
    print("=" * 60)
    
    # Get ALL non-dead tokens without supply data using pagination
    print("\nFetching ALL non-dead tokens needing supply data...")
    all_tokens = []
    offset = 0
    limit = 1000  # Process 1000 at a time
    
    while True:
        result = supabase.table('crypto_calls').select(
            'id,ticker,contract_address,price_at_call,current_price,ath_price,circulating_supply,total_supply'
        ).neq('is_dead', True).is_('total_supply', 'null').not_.is_('contract_address', 'null').range(offset, offset + limit - 1).execute()
        
        if not result.data:
            break
            
        all_tokens.extend(result.data)
        print(f"  Fetched batch: {len(result.data)} tokens (total so far: {len(all_tokens)})")
        
        if len(result.data) < limit:
            break  # Last batch
            
        offset += limit
    
    tokens = all_tokens
    print(f"\nTotal tokens to process: {len(tokens)}")
    
    if not tokens:
        print("No tokens need processing")
        return
    
    # Process in batches
    total_updated = 0
    total_mcap_calculated = 0
    total_current_mcap_calculated = 0
    total_ath_mcap_calculated = 0
    
    for i in range(0, len(tokens), BATCH_SIZE):
        batch = tokens[i:i+BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (len(tokens) + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"\n[Batch {batch_num}/{total_batches}] Processing {len(batch)} tokens...")
        
        # Extract contract addresses
        addresses = [t['contract_address'].lower() for t in batch if t['contract_address']]
        
        if not addresses:
            continue
        
        # Fetch supply data from DexScreener
        supply_data = fetch_supply_data_batch(addresses)
        
        if not supply_data:
            print(f"  ⚠️ No data returned from DexScreener")
            continue
        
        # Update each token
        for token in batch:
            if not token['contract_address']:
                continue
            
            addr = token['contract_address'].lower()
            data = supply_data.get(addr)
            
            if data:
                update_fields = {
                    'total_supply': data['total_supply'],
                    'circulating_supply': data['circulating_supply'],
                    'supply_updated_at': datetime.utcnow().isoformat()
                }
                
                # Check if circulating and total supply are similar (within 5%)
                circ = data['circulating_supply']
                total = data['total_supply']
                supply_similar = False
                
                if circ and total and total > 0:
                    diff_percent = abs(circ - total) / total * 100
                    supply_similar = diff_percent < 5  # Within 5% difference
                
                # Calculate market caps based on supply similarity
                if supply_similar:
                    # Supplies are similar, safe to use total supply for historical calculations
                    if token['price_at_call'] and total:
                        update_fields['market_cap_at_call'] = float(token['price_at_call']) * total
                        total_mcap_calculated += 1
                    
                    if token['ath_price'] and total:
                        update_fields['ath_market_cap'] = float(token['ath_price']) * total
                        total_ath_mcap_calculated += 1
                else:
                    # Supplies are different, can't assume they were same at launch
                    print(f"    ⚠️ {token['ticker']}: Supply mismatch ({diff_percent:.1f}% diff), skipping historical MCaps")
                
                # Current market cap can always use current circulating supply
                if token['current_price'] and circ:
                    update_fields['current_market_cap'] = float(token['current_price']) * circ
                    total_current_mcap_calculated += 1
                
                # Update database
                try:
                    supabase.table('crypto_calls').update(update_fields).eq('id', token['id']).execute()
                    
                    ticker = token['ticker']
                    if 'market_cap_at_call' in update_fields:
                        print(f"  ✅ {ticker}: Supply + MCaps updated (Entry: ${update_fields['market_cap_at_call']:,.0f})")
                    else:
                        print(f"  ✅ {ticker}: Supply updated")
                    
                    total_updated += 1
                except Exception as e:
                    print(f"  ❌ {token['ticker']}: {e}")
        
        # Rate limiting
        time.sleep(1)  # 1 second between batches
    
    # Summary
    print("\n" + "=" * 60)
    print("Processing Complete!")
    print(f"Tokens updated: {total_updated}")
    print(f"Market cap at call calculated: {total_mcap_calculated}")
    print(f"Current market cap calculated: {total_current_mcap_calculated}")
    print(f"ATH market cap calculated: {total_ath_mcap_calculated}")
    print("=" * 60)
    
    # Show sample results
    if total_updated > 0:
        print("\nSample of updated tokens:")
        sample = supabase.table('crypto_calls').select(
            'ticker,total_supply,market_cap_at_call,current_market_cap,ath_market_cap'
        ).not_.is_('market_cap_at_call', 'null').order('supply_updated_at', desc=True).limit(5).execute()
        
        for token in sample.data:
            print(f"  {token['ticker']}:")
            print(f"    Total Supply: {token['total_supply']/1000000:.1f}M")
            if token['market_cap_at_call']:
                print(f"    MC at Call: ${token['market_cap_at_call']:,.0f}")
            if token['current_market_cap']:
                print(f"    Current MC: ${token['current_market_cap']:,.0f}")
            if token['ath_market_cap']:
                print(f"    ATH MC: ${token['ath_market_cap']:,.0f}")

if __name__ == "__main__":
    process_tokens()