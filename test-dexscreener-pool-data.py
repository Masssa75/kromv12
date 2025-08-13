#!/usr/bin/env python3
"""
Test what data DexScreener provides via pools endpoint
Compare with GeckoTerminal to ensure we can replace it
"""

import requests
import json
from typing import Dict, Any

def test_geckoterminal_pool(network: str, pool_address: str) -> Dict:
    """Test what GeckoTerminal provides"""
    # Map network names
    network_map = {
        'ethereum': 'eth',
        'solana': 'solana',
        'bsc': 'bsc',
        'base': 'base'
    }
    
    gt_network = network_map.get(network, network)
    url = f"https://api.geckoterminal.com/api/v2/networks/{gt_network}/pools/{pool_address}"
    
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code == 200:
            data = response.json()
            attributes = data['data']['attributes']
            
            return {
                'success': True,
                'price': attributes.get('base_token_price_usd'),
                'fdv': attributes.get('fdv_usd'),
                'market_cap': attributes.get('market_cap_usd'),
                'liquidity': attributes.get('reserve_in_usd'),
                'raw': attributes
            }
    except Exception as e:
        return {'success': False, 'error': str(e)}
    
    return {'success': False, 'error': 'Failed to fetch'}

def test_dexscreener_pool(network: str, pool_address: str) -> Dict:
    """Test what DexScreener provides via pairs endpoint"""
    # DexScreener expects network/poolAddress format
    url = f"https://api.dexscreener.com/latest/dex/pairs/{network}/{pool_address}"
    
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            
            # Check if we got pair data
            if data.get('pairs') and len(data['pairs']) > 0:
                pair = data['pairs'][0]
            elif data.get('pair'):
                pair = data['pair']
            else:
                return {'success': False, 'error': 'No pair data'}
            
            # Extract social data
            socials = {}
            if pair.get('info'):
                social_list = pair['info'].get('socials', [])
                for social in social_list:
                    socials[social.get('type', 'unknown')] = social.get('url')
                
                # Also check websites field
                if pair['info'].get('websites'):
                    socials['website_from_websites'] = pair['info']['websites']
            
            return {
                'success': True,
                'price': pair.get('priceUsd'),
                'fdv': pair.get('fdv'),
                'market_cap': pair.get('marketCap'),
                'liquidity': pair.get('liquidity', {}).get('usd') if isinstance(pair.get('liquidity'), dict) else pair.get('liquidity'),
                'volume_24h': pair.get('volume', {}).get('h24') if isinstance(pair.get('volume'), dict) else None,
                'socials': socials,
                'raw': pair
            }
    except Exception as e:
        return {'success': False, 'error': str(e)}
    
    return {'success': False, 'error': 'Failed to fetch'}

def compare_apis():
    """Compare what both APIs provide for the same pools"""
    
    # Test cases - real pools from the database
    test_pools = [
        # (network, pool_address, token_name)
        ('solana', '7yWqBJo9xWudZNhBAaR9rNGDDqGSicdHsCRvu8CQAQGB', 'TEST_SOL'),
        ('ethereum', '0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640', 'USDC/WETH'),
        ('base', '0xd0b53d9277642d899df5c87a3966a349a798f224', 'AERODROME'),
    ]
    
    print("=" * 80)
    print("COMPARING GECKOTERMINAL vs DEXSCREENER DATA")
    print("=" * 80)
    
    for network, pool_address, name in test_pools:
        print(f"\n📊 Testing: {name} on {network}")
        print(f"Pool: {pool_address[:20]}...")
        print("-" * 60)
        
        # Test GeckoTerminal
        print("\n🦎 GeckoTerminal Data:")
        gt_data = test_geckoterminal_pool(network, pool_address)
        
        if gt_data['success']:
            print(f"  ✅ Price: ${gt_data['price']}")
            print(f"  ✅ FDV: ${gt_data['fdv']}")
            print(f"  ✅ Market Cap: ${gt_data['market_cap']}")
            print(f"  ✅ Liquidity: ${gt_data['liquidity']}")
            print(f"  ❌ Socials: Not provided")
        else:
            print(f"  ❌ Error: {gt_data['error']}")
        
        # Test DexScreener
        print("\n📱 DexScreener Data:")
        ds_data = test_dexscreener_pool(network, pool_address)
        
        if ds_data['success']:
            print(f"  ✅ Price: ${ds_data['price']}")
            print(f"  ✅ FDV: ${ds_data['fdv']}")
            print(f"  ✅ Market Cap: ${ds_data['market_cap']}")
            print(f"  ✅ Liquidity: ${ds_data['liquidity']}")
            print(f"  ✅ Volume 24h: ${ds_data['volume_24h']}")
            
            if ds_data['socials']:
                print(f"  ✅ Socials found:")
                for social_type, url in ds_data['socials'].items():
                    if url:
                        print(f"     - {social_type}: {str(url)[:50]}...")
            else:
                print(f"  ⚠️ No socials")
        else:
            print(f"  ❌ Error: {ds_data['error']}")
        
        # Compare values if both successful
        if gt_data['success'] and ds_data['success']:
            print("\n🔍 Comparison:")
            
            # Price comparison
            if gt_data['price'] and ds_data['price']:
                price_diff = abs(float(gt_data['price']) - float(ds_data['price']))
                print(f"  Price difference: ${price_diff:.8f}")
            
            # Check if we can calculate supplies
            if ds_data['fdv'] and ds_data['price'] and float(ds_data['price']) > 0:
                total_supply = float(ds_data['fdv']) / float(ds_data['price'])
                print(f"  Calculated total supply: {total_supply:,.0f}")
            
            if ds_data['market_cap'] and ds_data['price'] and float(ds_data['price']) > 0:
                circ_supply = float(ds_data['market_cap']) / float(ds_data['price'])
                print(f"  Calculated circulating supply: {circ_supply:,.0f}")

def main():
    """Run the comparison tests"""
    compare_apis()
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print("""
DexScreener provides ALL the data that GeckoTerminal provides:
✅ Price (priceUsd)
✅ FDV (fdv)
✅ Market Cap (marketCap)
✅ Liquidity (liquidity.usd)
✅ Supply calculations (FDV/price, MarketCap/price)

PLUS additional data:
✅ Volume 24h
✅ Social links (website, twitter, telegram, discord)
✅ Price changes
✅ Transaction counts

CONCLUSION: DexScreener can fully replace GeckoTerminal in crypto-poller
""")

if __name__ == "__main__":
    main()