#!/usr/bin/env python3
"""
Market Cap Updater V2 - DexScreener Batch Processing
=====================================================
Uses DexScreener API batch calls to efficiently populate market cap data.
DexScreener allows multiple tokens per API call (comma-separated addresses).
"""

import os
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# Suppress SSL warnings
import warnings
warnings.filterwarnings("ignore", message="urllib3 v2 only supports OpenSSL")

import requests
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Initialize Supabase client (using service role key for writes with RLS enabled)
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

# DexScreener batch size (they support large batches)
BATCH_SIZE = 30  # Conservative batch size to avoid URL length limits

def get_dexscreener_batch_data(contract_addresses: List[str]) -> Dict[str, Any]:
    """
    Fetch market data from DexScreener for multiple tokens in one API call.
    Returns a dictionary mapping contract addresses to their market data.
    """
    try:
        # Join addresses with commas for batch request
        addresses_param = ','.join(contract_addresses)
        url = f"https://api.dexscreener.com/latest/dex/tokens/{addresses_param}"
        
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Process the response and map by contract address
            result = {}
            
            if 'pairs' in data and data['pairs']:
                for pair in data['pairs']:
                    # Get the base token (the token we're interested in)
                    base_token = pair.get('baseToken', {})
                    contract = base_token.get('address', '').lower()
                    
                    if contract:
                        # If we already have this token, keep the pair with highest liquidity
                        if contract in result:
                            existing_liq = float(result[contract].get('liquidity', {}).get('usd', 0) or 0)
                            new_liq = float(pair.get('liquidity', {}).get('usd', 0) or 0)
                            if new_liq <= existing_liq:
                                continue
                        
                        # Extract the data we need
                        fdv = pair.get('fdv')
                        market_cap = pair.get('marketCap') 
                        price = float(pair.get('priceUsd', 0))
                        
                        # Calculate supplies if we have the data
                        total_supply = None
                        circulating_supply = None
                        
                        if fdv and price > 0:
                            total_supply = fdv / price
                        
                        if market_cap and price > 0:
                            circulating_supply = market_cap / price
                        
                        result[contract] = {
                            'ticker': base_token.get('symbol'),
                            'fdv': fdv,
                            'market_cap': market_cap,
                            'price': price,
                            'total_supply': total_supply,
                            'circulating_supply': circulating_supply,
                            'liquidity_usd': pair.get('liquidity', {}).get('usd'),
                            'volume_24h': pair.get('volume', {}).get('h24')
                        }
            
            return result
            
    except Exception as e:
        print(f"Error fetching DexScreener batch data: {e}")
    
    return {}

def update_tokens_batch(tokens: List[Dict[str, Any]]) -> int:
    """
    Update a batch of tokens with market cap data from DexScreener.
    Returns the number of successfully updated tokens.
    """
    # Extract contract addresses
    addresses = [t['contract_address'].lower() for t in tokens if t['contract_address']]
    
    if not addresses:
        return 0
    
    # Fetch data from DexScreener
    print(f"  📡 Fetching data for {len(addresses)} tokens from DexScreener...")
    market_data = get_dexscreener_batch_data(addresses)
    
    if not market_data:
        print(f"  ⚠️ No data returned from DexScreener")
        return 0
    
    # Update each token
    success_count = 0
    for token in tokens:
        if not token['contract_address']:
            continue
            
        contract = token['contract_address'].lower()
        data = market_data.get(contract)
        
        if data:
            # Prepare update data
            update_data = {
                'supply_updated_at': datetime.utcnow().isoformat()
            }
            
            # Add supply data if available
            if data['circulating_supply']:
                update_data['circulating_supply'] = data['circulating_supply']
            
            if data['total_supply']:
                update_data['total_supply'] = data['total_supply']
            
            # Calculate market cap
            if data['market_cap']:
                update_data['current_market_cap'] = data['market_cap']
            elif data['circulating_supply'] and token['current_price']:
                # Calculate from our price and their supply
                update_data['current_market_cap'] = token['current_price'] * data['circulating_supply']
            
            # Also update volume and liquidity if available
            if data['volume_24h']:
                update_data['volume_24h'] = data['volume_24h']
            
            if data['liquidity_usd']:
                update_data['liquidity_usd'] = data['liquidity_usd']
            
            # Update database
            try:
                result = supabase.table('crypto_calls').update(update_data).eq('id', token['id']).execute()
                print(f"    ✅ {token['ticker']}: MC=${update_data.get('current_market_cap', 0):,.0f}")
                success_count += 1
            except Exception as e:
                print(f"    ❌ {token['ticker']}: Database update failed - {e}")
        else:
            print(f"    ⚠️ {token['ticker']}: No data from DexScreener")
    
    return success_count

def main():
    """Main function to update market cap data for all tokens."""
    print("=" * 60)
    print("KROM Market Cap Updater V2 - DexScreener Batch Processing")
    print("=" * 60)
    
    # Get tokens that need market cap data
    # Prioritize tokens with prices but no market cap
    print("\nFetching tokens from database...")
    query = supabase.table('crypto_calls').select(
        'id,ticker,contract_address,network,current_price'
    ).not_.is_('current_price', 'null').is_('current_market_cap', 'null').order('created_at', desc=True)
    
    result = query.execute()
    tokens = result.data[:60]  # Limit to 60 tokens for testing (2 batches)
    
    print(f"Found {len(tokens)} tokens needing market cap data")
    
    if not tokens:
        print("No tokens to process")
        return
    
    # Process in batches
    total_success = 0
    total_processed = 0
    
    for i in range(0, len(tokens), BATCH_SIZE):
        batch = tokens[i:i+BATCH_SIZE]
        batch_num = (i // BATCH_SIZE) + 1
        total_batches = (len(tokens) + BATCH_SIZE - 1) // BATCH_SIZE
        
        print(f"\n[Batch {batch_num}/{total_batches}] Processing {len(batch)} tokens...")
        
        success = update_tokens_batch(batch)
        total_success += success
        total_processed += len(batch)
        
        print(f"  Batch complete: {success}/{len(batch)} successful")
        
        # Rate limiting between batches
        if i + BATCH_SIZE < len(tokens):
            time.sleep(1)  # 1 second between batches
    
    # Final summary
    print("\n" + "=" * 60)
    print(f"Processing complete!")
    print(f"Total tokens processed: {total_processed}")
    print(f"Successfully updated: {total_success}")
    print(f"Success rate: {(total_success/total_processed*100):.1f}%")
    print("=" * 60)
    
    # Show sample of updated data
    print("\nSample of updated tokens:")
    sample_query = supabase.table('crypto_calls').select(
        'ticker,current_market_cap,circulating_supply'
    ).not_.is_('current_market_cap', 'null').order('supply_updated_at', desc=True).limit(5)
    
    sample_result = sample_query.execute()
    for token in sample_result.data:
        print(f"  {token['ticker']}: MC=${token['current_market_cap']:,.0f}, Supply={token['circulating_supply']:,.0f}")

if __name__ == "__main__":
    main()