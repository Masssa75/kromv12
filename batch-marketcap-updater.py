#!/usr/bin/env python3
"""
Market Cap Updater for KROM Crypto Calls
=========================================
Populates market cap data by fetching circulating supply from multiple sources:
1. CoinMarketCap API (for major tokens)
2. DexScreener API (calculate from FDV if available)
3. GeckoTerminal API (estimate from liquidity/volume patterns)
"""

import os
import sys
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
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

# API Keys
CMC_API_KEY = os.getenv('COINMARKETCAP_API_KEY')
GECKO_API_KEY = os.getenv('GECKO_TERMINAL_API_KEY')

# Chain ID mappings for different APIs
CHAIN_MAPPINGS = {
    'ethereum': {'cmc': 'ethereum', 'dexscreener': 'ethereum', 'gecko': 'eth'},
    'solana': {'cmc': 'solana', 'dexscreener': 'solana', 'gecko': 'solana'},
    'bsc': {'cmc': 'binance-smart-chain', 'dexscreener': 'bsc', 'gecko': 'bsc'},
    'base': {'cmc': 'base', 'dexscreener': 'base', 'gecko': 'base'},
    'arbitrum': {'cmc': 'arbitrum', 'dexscreener': 'arbitrum', 'gecko': 'arbitrum'},
    'polygon': {'cmc': 'polygon', 'dexscreener': 'polygon', 'gecko': 'polygon'},
    'avalanche': {'cmc': 'avalanche', 'dexscreener': 'avalanche', 'gecko': 'avax'}
}

def get_cmc_supply_data(contract_address: str, network: str) -> Optional[Dict[str, Any]]:
    """
    Fetch supply data from CoinMarketCap API.
    Returns circulating_supply, total_supply, max_supply if available.
    """
    if not CMC_API_KEY:
        return None
    
    try:
        # First try to get by contract address
        headers = {
            'X-CMC_PRO_API_KEY': CMC_API_KEY,
            'Accept': 'application/json'
        }
        
        # Map network to CMC platform ID
        platform_map = {
            'ethereum': '1',
            'bsc': '56',
            'polygon': '137',
            'avalanche': '43114',
            'arbitrum': '42161',
            'base': '8453',
            'solana': '5426'  # Solana's platform ID on CMC
        }
        
        platform_id = platform_map.get(network)
        if not platform_id:
            return None
        
        # Try to get token info by contract address
        url = 'https://pro-api.coinmarketcap.com/v2/cryptocurrency/info'
        params = {
            'address': contract_address
        }
        
        response = requests.get(url, headers=headers, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']:
                # Get the first token data (should only be one for specific address)
                token_data = list(data['data'].values())[0]
                
                # Now get the latest quote data with supply info
                quote_url = 'https://pro-api.coinmarketcap.com/v2/cryptocurrency/quotes/latest'
                quote_params = {
                    'id': token_data['id']
                }
                
                quote_response = requests.get(quote_url, headers=headers, params=quote_params, timeout=10)
                
                if quote_response.status_code == 200:
                    quote_data = quote_response.json()
                    if 'data' in quote_data and str(token_data['id']) in quote_data['data']:
                        supply_info = quote_data['data'][str(token_data['id'])]
                        return {
                            'circulating_supply': supply_info.get('circulating_supply'),
                            'total_supply': supply_info.get('total_supply'),
                            'max_supply': supply_info.get('max_supply'),
                            'source': 'coinmarketcap'
                        }
    except Exception as e:
        print(f"Error fetching CMC data: {e}")
    
    return None

def get_dexscreener_supply_estimate(contract_address: str, network: str) -> Optional[Dict[str, Any]]:
    """
    Fetch market data from DexScreener and estimate supply from FDV.
    """
    try:
        chain = CHAIN_MAPPINGS.get(network, {}).get('dexscreener', network)
        url = f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}"
        
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'pairs' in data and data['pairs']:
                # Get the pair with highest liquidity
                pairs = sorted(data['pairs'], key=lambda x: float(x.get('liquidity', {}).get('usd', 0) or 0), reverse=True)
                best_pair = pairs[0]
                
                fdv = best_pair.get('fdv')
                market_cap = best_pair.get('marketCap')
                price = float(best_pair.get('priceUsd', 0))
                
                if fdv and price > 0:
                    # Calculate total supply from FDV
                    total_supply = fdv / price
                    
                    # If we have market cap, calculate circulating supply
                    circulating_supply = None
                    if market_cap and market_cap > 0:
                        circulating_supply = market_cap / price
                    
                    return {
                        'circulating_supply': circulating_supply,
                        'total_supply': total_supply,
                        'max_supply': None,  # DexScreener doesn't provide this
                        'fdv': fdv,
                        'market_cap': market_cap,
                        'source': 'dexscreener_estimate'
                    }
    except Exception as e:
        print(f"Error fetching DexScreener data: {e}")
    
    return None

def get_geckoterminal_market_data(pool_address: str, network: str) -> Optional[Dict[str, Any]]:
    """
    Fetch pool data from GeckoTerminal to get FDV and market cap.
    """
    try:
        chain = CHAIN_MAPPINGS.get(network, {}).get('gecko', network)
        url = f"https://api.geckoterminal.com/api/v2/networks/{chain}/pools/{pool_address}"
        
        headers = {}
        if GECKO_API_KEY:
            headers['Authorization'] = f'Bearer {GECKO_API_KEY}'
        
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and 'attributes' in data['data']:
                attrs = data['data']['attributes']
                
                fdv = attrs.get('fdv_usd')
                market_cap = attrs.get('market_cap_usd')
                price = float(attrs.get('base_token_price_usd', 0))
                
                if fdv and price > 0:
                    # Calculate supplies from FDV and market cap
                    total_supply = None
                    circulating_supply = None
                    
                    if isinstance(fdv, (int, float)):
                        total_supply = fdv / price
                    
                    if market_cap and isinstance(market_cap, (int, float)):
                        circulating_supply = market_cap / price
                    
                    return {
                        'circulating_supply': circulating_supply,
                        'total_supply': total_supply,
                        'max_supply': None,
                        'fdv': fdv,
                        'market_cap': market_cap,
                        'source': 'geckoterminal'
                    }
    except Exception as e:
        print(f"Error fetching GeckoTerminal data: {e}")
    
    return None

def calculate_market_cap(price: float, circulating_supply: float) -> float:
    """Calculate market cap from price and circulating supply."""
    if price and circulating_supply:
        return price * circulating_supply
    return None

def update_token_supply_and_market_cap(token: Dict[str, Any]) -> bool:
    """
    Update a single token's supply data and calculate market cap.
    """
    token_id = token['id']
    contract_address = token['contract_address']
    pool_address = token['pool_address']
    network = token['network']
    current_price = token['current_price']
    ticker = token['ticker']
    
    print(f"\nProcessing {ticker} ({network})")
    
    supply_data = None
    
    # Try multiple sources in order of preference
    # 1. Try CoinMarketCap (most reliable for major tokens)
    if contract_address:
        supply_data = get_cmc_supply_data(contract_address, network)
        if supply_data:
            print(f"  ✅ Found on CoinMarketCap")
    
    # 2. Try DexScreener (good for DEX tokens)
    if not supply_data and contract_address:
        supply_data = get_dexscreener_supply_estimate(contract_address, network)
        if supply_data:
            print(f"  ✅ Estimated from DexScreener FDV")
    
    # 3. Try GeckoTerminal with pool address (fallback)
    if not supply_data and pool_address:
        supply_data = get_geckoterminal_market_data(pool_address, network)
        if supply_data:
            print(f"  ✅ Got data from GeckoTerminal")
    
    if supply_data:
        # Calculate market caps
        update_data = {
            'circulating_supply': supply_data.get('circulating_supply'),
            'total_supply': supply_data.get('total_supply'),
            'max_supply': supply_data.get('max_supply'),
            'supply_updated_at': datetime.utcnow().isoformat()
        }
        
        # Calculate current market cap if we have price and circulating supply
        if current_price and supply_data.get('circulating_supply'):
            update_data['current_market_cap'] = calculate_market_cap(
                current_price, 
                supply_data['circulating_supply']
            )
            print(f"  💰 Market Cap: ${update_data['current_market_cap']:,.2f}")
        elif supply_data.get('market_cap'):
            # Use market cap from API if available
            update_data['current_market_cap'] = supply_data['market_cap']
            print(f"  💰 Market Cap (from API): ${update_data['current_market_cap']:,.2f}")
        
        # Update database
        try:
            result = supabase.table('crypto_calls').update(update_data).eq('id', token_id).execute()
            print(f"  ✅ Updated database (source: {supply_data.get('source', 'unknown')})")
            return True
        except Exception as e:
            print(f"  ❌ Database update failed: {e}")
            return False
    else:
        print(f"  ⚠️ No supply data found")
        return False

def main():
    """Main function to update market cap data for all tokens."""
    print("=" * 60)
    print("KROM Market Cap Updater")
    print("=" * 60)
    
    # Get tokens that need market cap data
    # Prioritize tokens with prices but no market cap
    query = supabase.table('crypto_calls').select(
        'id,ticker,contract_address,pool_address,network,current_price,price_at_call'
    ).not_.is_('current_price', 'null').is_('current_market_cap', 'null').order('created_at', desc=True)
    
    result = query.execute()
    tokens = result.data
    
    print(f"\nFound {len(tokens)} tokens needing market cap data")
    
    if not tokens:
        print("No tokens to process")
        return
    
    # Process tokens
    success_count = 0
    processed_count = 0
    
    # Limit for testing
    test_limit = 5
    for i, token in enumerate(tokens[:test_limit], 1):  # Process first 5 for testing
        print(f"\n[{i}/{min(test_limit, len(tokens))}]", end="")
        
        success = update_token_supply_and_market_cap(token)
        if success:
            success_count += 1
        processed_count += 1
        
        # Rate limiting
        if processed_count % 10 == 0:
            print(f"\n--- Processed {processed_count} tokens, {success_count} successful ---")
            time.sleep(2)  # Brief pause every 10 tokens
        else:
            time.sleep(0.5)  # Small delay between requests
    
    # Final summary
    print("\n" + "=" * 60)
    print(f"Processing complete!")
    print(f"Processed: {processed_count} tokens")
    print(f"Successfully updated: {success_count} tokens")
    print(f"Success rate: {(success_count/processed_count*100):.1f}%")
    print("=" * 60)

if __name__ == "__main__":
    main()