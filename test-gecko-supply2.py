#!/usr/bin/env python3
"""
Test GeckoTerminal API with an actual pool from our database
"""

import os
import warnings
warnings.filterwarnings("ignore")
from dotenv import load_dotenv
from supabase import create_client
import requests

load_dotenv()

# Get a real pool address from our database
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

# Get a recent token with pool address
result = supabase.table('crypto_calls').select(
    'ticker,network,pool_address'
).not_.is_('pool_address', 'null').order('created_at', desc=True).limit(1).execute()

if result.data:
    token = result.data[0]
    print(f"Testing with {token['ticker']} on {token['network']}")
    print(f"Pool address: {token['pool_address']}\n")
    
    # Map network name
    network_map = {
        'ethereum': 'eth',
        'solana': 'solana',
        'bsc': 'bsc',
        'polygon': 'polygon',
        'arbitrum': 'arbitrum',
        'base': 'base'
    }
    
    network = network_map.get(token['network'].lower(), token['network'].lower())
    url = f"https://api.geckoterminal.com/api/v2/networks/{network}/pools/{token['pool_address']}"
    
    print(f"URL: {url}\n")
    
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    
    if response.status_code == 200:
        data = response.json()
        attributes = data['data']['attributes']
        
        print("GeckoTerminal Response:")
        print(f"  Token name: {attributes.get('name')}")
        print(f"  Price USD: ${attributes.get('base_token_price_usd')}")
        print(f"  FDV USD: ${float(attributes.get('fdv_usd', 0)):,.0f}" if attributes.get('fdv_usd') else "  FDV USD: None")
        print(f"  Market Cap USD: ${float(attributes.get('market_cap_usd', 0)):,.0f}" if attributes.get('market_cap_usd') else "  Market Cap USD: None")
        
        # Calculate supplies
        price = float(attributes.get('base_token_price_usd', 0))
        fdv = float(attributes.get('fdv_usd', 0))
        market_cap = float(attributes.get('market_cap_usd') or 0)
        
        if price > 0:
            print("\nCalculated Supplies:")
            if fdv > 0:
                total_supply = fdv / price
                print(f"  Total Supply: {total_supply:,.0f}")
            
            if market_cap > 0:
                circ_supply = market_cap / price
                print(f"  Circulating Supply: {circ_supply:,.0f}")
                
            if fdv > 0 and market_cap > 0:
                diff_percent = abs(market_cap - fdv) / fdv * 100
                print(f"\n  Supply difference: {diff_percent:.1f}%")
                if diff_percent < 5:
                    print("  ✅ Supplies are similar - safe to calculate market_cap_at_call")
                else:
                    print("  ⚠️ Supplies differ - skip market_cap_at_call")
    else:
        print(f"Error: {response.status_code}")
        print(response.text[:500])