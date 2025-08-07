#!/usr/bin/env python3
"""
Process Dead Tokens - Check if they're trading again and backfill data
=====================================================================
Uses GeckoTerminal API (1 token at a time) to check dead tokens
If trading again: fetches supply data and revives the token
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

# GeckoTerminal network mapping
NETWORK_MAP = {
    'ethereum': 'eth',
    'solana': 'solana',
    'bsc': 'bsc',
    'polygon': 'polygon',
    'arbitrum': 'arbitrum',
    'base': 'base',
    'optimism': 'optimism',
    'avalanche': 'avalanche'
}

def fetch_token_from_geckoterminal(network, pool_address):
    """Fetch token data from GeckoTerminal API"""
    gecko_network = NETWORK_MAP.get(network.lower())
    if not gecko_network:
        return None
    
    url = f"https://api.geckoterminal.com/api/v2/networks/{gecko_network}/pools/{pool_address}"
    
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        if response.status_code == 200:
            data = response.json()
            attributes = data.get('data', {}).get('attributes', {})
            
            if attributes and attributes.get('base_token_price_usd'):
                price = float(attributes.get('base_token_price_usd', 0))
                fdv = float(attributes.get('fdv_usd', 0))
                market_cap = float(attributes.get('market_cap_usd') or 0)
                volume_24h = float(attributes.get('volume_usd', {}).get('h24', 0))
                liquidity = float(attributes.get('reserve_in_usd', 0))
                
                # Calculate supplies
                total_supply = None
                circulating_supply = None
                
                if price > 0:
                    if fdv > 0:
                        total_supply = fdv / price
                    if market_cap > 0:
                        circulating_supply = market_cap / price
                    elif total_supply:
                        circulating_supply = total_supply  # Assume fully circulating
                
                return {
                    'is_trading': True,
                    'current_price': price,
                    'fdv': fdv,
                    'market_cap': market_cap,
                    'total_supply': total_supply,
                    'circulating_supply': circulating_supply,
                    'volume_24h': volume_24h,
                    'liquidity_usd': liquidity
                }
        
        return {'is_trading': False}
    
    except Exception as e:
        print(f"    Error fetching from GeckoTerminal: {e}")
        return None

def process_dead_tokens():
    """Main processing function"""
    print("=" * 60)
    print("Dead Token Processor - Revival Check")
    print("=" * 60)
    
    # Get dead tokens with pool addresses
    print("\nFetching dead tokens...")
    result = supabase.table('crypto_calls').select(
        'id,ticker,network,contract_address,pool_address,price_at_call,'
        'total_supply,circulating_supply,is_dead'
    ).eq('is_dead', True).not_.is_('pool_address', 'null').limit(5000).execute()  # Process all dead tokens
    
    dead_tokens = result.data
    print(f"Found {len(dead_tokens)} dead tokens to check")
    
    if not dead_tokens:
        print("No dead tokens to process")
        return
    
    # Process statistics
    revived_count = 0
    still_dead_count = 0
    error_count = 0
    
    print("\nProcessing dead tokens (1 token per API call)...")
    print("-" * 60)
    
    for i, token in enumerate(dead_tokens, 1):
        # Progress indicator every 10 tokens
        if i % 10 == 0:
            elapsed = (i * 2) / 60  # minutes elapsed
            remaining = ((len(dead_tokens) - i) * 2) / 60  # minutes remaining
            print(f"\nProgress: {i}/{len(dead_tokens)} tokens ({elapsed:.1f} min elapsed, ~{remaining:.1f} min remaining)")
            print(f"  Revived: {revived_count}, Still dead: {still_dead_count}, Errors: {error_count}")
        
        ticker = token['ticker']
        network = token['network']
        pool_address = token['pool_address']
        
        # Rate limiting - GeckoTerminal allows ~30 req/min
        time.sleep(2)  # 2 seconds between calls = 30 calls/min
        
        # Fetch from GeckoTerminal
        gecko_data = fetch_token_from_geckoterminal(network, pool_address)
        
        if not gecko_data:
            error_count += 1
            continue
        
        if gecko_data['is_trading']:
            # Token is trading again! Revive it
            print(f"\n✅ REVIVED: {ticker} ({network})")
            print(f"   Price: ${gecko_data['current_price']:.8f}")
            print(f"   Volume 24h: ${gecko_data['volume_24h']:,.0f}")
            print(f"   Liquidity: ${gecko_data['liquidity_usd']:,.0f}")
            
            # Prepare update data
            update_data = {
                'is_dead': False,
                'current_price': gecko_data['current_price'],
                'volume_24h': gecko_data['volume_24h'],
                'liquidity_usd': gecko_data['liquidity_usd'],
                'price_updated_at': datetime.utcnow().isoformat()
            }
            
            # Add supply data if we got it
            if gecko_data['total_supply']:
                update_data['total_supply'] = gecko_data['total_supply']
                update_data['supply_updated_at'] = datetime.utcnow().isoformat()
                
                # Calculate market_cap_at_call if we have price_at_call
                if token['price_at_call'] and gecko_data['total_supply']:
                    # Check if supplies are similar (within 5%)
                    if gecko_data['circulating_supply']:
                        diff = abs(gecko_data['circulating_supply'] - gecko_data['total_supply'])
                        diff_percent = (diff / gecko_data['total_supply'] * 100) if gecko_data['total_supply'] > 0 else 0
                        if diff_percent < 5:
                            update_data['market_cap_at_call'] = float(token['price_at_call']) * gecko_data['total_supply']
            
            if gecko_data['circulating_supply']:
                update_data['circulating_supply'] = gecko_data['circulating_supply']
                # Calculate current market cap
                update_data['current_market_cap'] = gecko_data['current_price'] * gecko_data['circulating_supply']
            
            # Update database
            try:
                supabase.table('crypto_calls').update(update_data).eq('id', token['id']).execute()
                revived_count += 1
                
                if gecko_data['total_supply']:
                    print(f"   Supply: {gecko_data['total_supply']:,.0f}")
                if update_data.get('market_cap_at_call'):
                    print(f"   Market Cap at Call: ${update_data['market_cap_at_call']:,.0f}")
                if update_data.get('current_market_cap'):
                    print(f"   Current Market Cap: ${update_data['current_market_cap']:,.0f}")
                    
            except Exception as e:
                print(f"   ❌ Failed to update database: {e}")
                error_count += 1
        else:
            # Still dead
            still_dead_count += 1
            # Optionally show progress dots for dead tokens
            print(".", end="", flush=True)
    
    # Summary
    print("\n\n" + "=" * 60)
    print("Processing Complete!")
    print("=" * 60)
    print(f"Tokens checked: {len(dead_tokens)}")
    print(f"Revived tokens: {revived_count} 🎉")
    print(f"Still dead: {still_dead_count}")
    print(f"Errors: {error_count}")
    
    if revived_count > 0:
        print("\n✨ Revived tokens now have:")
        print("  - Current price and volume data")
        print("  - Supply data (total & circulating)")
        print("  - Market cap calculations")
        print("  - is_dead flag set to false")
        print("\nThey will now be included in ultra-tracker updates!")
    
    print("=" * 60)

if __name__ == "__main__":
    # Show warning about processing time
    print("\n⚠️  This script processes tokens one at a time via GeckoTerminal API")
    print("Processing time: ~2 seconds per token (rate limited)")
    print("For 1000 tokens: ~33 minutes")
    
    response = input("\nProceed? (y/n): ")
    if response.lower() == 'y':
        process_dead_tokens()
    else:
        print("Cancelled.")