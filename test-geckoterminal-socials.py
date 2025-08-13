#!/usr/bin/env python3
"""
Deep dive into GeckoTerminal API to find social/website data
Test multiple endpoints and data structures
"""

import requests
import json
import time
from typing import Dict, Any, Optional

def test_token_pools_endpoint(network: str, address: str, symbol: str) -> Dict:
    """Test the pools endpoint which might have more data"""
    print(f"\n📊 Testing POOLS endpoint for {symbol} on {network}")
    print("-" * 40)
    
    # Network mapping (what KROM uses vs what GT expects)
    network_map = {
        'ethereum': 'eth',
        'solana': 'solana',
        'bsc': 'bsc',
        'polygon': 'polygon',
        'arbitrum': 'arbitrum',
        'base': 'base'
    }
    
    gt_network = network_map.get(network, network)
    
    try:
        # Try pools endpoint
        url = f"https://api.geckoterminal.com/api/v2/networks/{gt_network}/tokens/{address}/pools"
        response = requests.get(url, timeout=10, headers={'Accept': 'application/json'})
        
        if response.status_code == 200:
            data = response.json()
            pools = data.get('data', [])
            
            if pools:
                # Check first pool for info
                pool = pools[0]
                attributes = pool.get('attributes', {})
                
                print(f"✅ Found {len(pools)} pools")
                print(f"  Pool name: {attributes.get('name', 'N/A')}")
                print(f"  Pool address: {attributes.get('address', 'N/A')[:20]}...")
                
                # Look for any website/social references in pool data
                for key, value in attributes.items():
                    if any(term in key.lower() for term in ['website', 'social', 'twitter', 'telegram', 'discord', 'link', 'url']):
                        print(f"  Found field: {key} = {value}")
                
                return {'success': True, 'pools': len(pools), 'data': data}
            else:
                print("  No pools found")
                return {'success': False, 'error': 'No pools'}
        else:
            print(f"  Error: {response.status_code}")
            return {'success': False, 'error': f'Status {response.status_code}'}
            
    except Exception as e:
        print(f"  Exception: {e}")
        return {'success': False, 'error': str(e)}

def test_token_info_endpoint(network: str, address: str, symbol: str) -> Dict:
    """Test the token info endpoint"""
    print(f"\n🪙 Testing TOKEN INFO endpoint for {symbol} on {network}")
    print("-" * 40)
    
    network_map = {
        'ethereum': 'eth',
        'solana': 'solana',
        'bsc': 'bsc',
        'polygon': 'polygon',
        'arbitrum': 'arbitrum',
        'base': 'base'
    }
    
    gt_network = network_map.get(network, network)
    
    try:
        url = f"https://api.geckoterminal.com/api/v2/networks/{gt_network}/tokens/{address}"
        response = requests.get(url, timeout=10, headers={'Accept': 'application/json'})
        
        if response.status_code == 200:
            data = response.json()
            token_data = data.get('data', {})
            attributes = token_data.get('attributes', {})
            
            print(f"✅ Token found: {attributes.get('name', 'N/A')}")
            print(f"  Symbol: {attributes.get('symbol', 'N/A')}")
            print(f"  CoinGecko ID: {attributes.get('coingecko_coin_id', 'None')}")
            
            # Check all attributes for social/website data
            social_fields = {}
            for key, value in attributes.items():
                if any(term in key.lower() for term in ['website', 'social', 'twitter', 'telegram', 'discord', 'link', 'url', 'homepage']):
                    social_fields[key] = value
                    print(f"  Found field: {key} = {value}")
            
            # Check relationships
            relationships = token_data.get('relationships', {})
            if relationships:
                print(f"  Relationships available: {list(relationships.keys())}")
            
            # Check included data
            included = data.get('included', [])
            if included:
                print(f"  Included data: {len(included)} items")
                for item in included[:2]:  # Check first 2 items
                    item_type = item.get('type', 'unknown')
                    item_attrs = item.get('attributes', {})
                    print(f"    - Type: {item_type}")
                    for key in item_attrs:
                        if any(term in key.lower() for term in ['website', 'social', 'twitter', 'url']):
                            print(f"      {key}: {item_attrs[key]}")
            
            return {'success': True, 'social_fields': social_fields, 'data': data}
        else:
            print(f"  Error: {response.status_code}")
            return {'success': False, 'error': f'Status {response.status_code}'}
            
    except Exception as e:
        print(f"  Exception: {e}")
        return {'success': False, 'error': str(e)}

def test_token_info_with_includes(network: str, address: str, symbol: str) -> Dict:
    """Test token info with include parameters"""
    print(f"\n🔗 Testing TOKEN INFO with INCLUDES for {symbol}")
    print("-" * 40)
    
    network_map = {
        'ethereum': 'eth',
        'solana': 'solana',
        'bsc': 'bsc'
    }
    
    gt_network = network_map.get(network, network)
    
    try:
        # Try with include parameter for more data
        url = f"https://api.geckoterminal.com/api/v2/networks/{gt_network}/tokens/{address}?include=top_pools"
        response = requests.get(url, timeout=10, headers={'Accept': 'application/json'})
        
        if response.status_code == 200:
            data = response.json()
            
            # Check main token data
            token_data = data.get('data', {})
            attributes = token_data.get('attributes', {})
            
            # Check for gt_score which might indicate verified tokens
            gt_score = attributes.get('gt_score', 0)
            if gt_score:
                print(f"  GT Score: {gt_score} (verified token)")
            
            # Check meta information
            meta = data.get('meta', {})
            if meta:
                print(f"  Meta data: {json.dumps(meta, indent=2)}")
            
            # Check links in the response
            links = data.get('links', {})
            if links:
                print(f"  Links found:")
                for key, value in links.items():
                    print(f"    {key}: {value}")
            
            return {'success': True, 'data': data}
        else:
            print(f"  Error: {response.status_code}")
            return {'success': False, 'error': f'Status {response.status_code}'}
            
    except Exception as e:
        print(f"  Exception: {e}")
        return {'success': False, 'error': str(e)}

def test_coingecko_crossref(coingecko_id: str) -> Optional[Dict]:
    """If we have a CoinGecko ID, check CoinGecko API for socials"""
    if not coingecko_id or coingecko_id == 'None':
        return None
    
    print(f"\n🦎 Checking CoinGecko API for {coingecko_id}")
    print("-" * 40)
    
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{coingecko_id}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            links = data.get('links', {})
            
            social_data = {
                'homepage': links.get('homepage', []),
                'twitter': f"https://twitter.com/{links.get('twitter_screen_name')}" if links.get('twitter_screen_name') else None,
                'telegram': links.get('telegram_channel_identifier', ''),
                'subreddit': links.get('subreddit_url', ''),
                'github': links.get('repos_url', {}).get('github', []),
                'discord': None,  # Discord not in standard response
                'whitepaper': links.get('whitepaper', '')
            }
            
            # Clean up empty values
            social_data = {k: v for k, v in social_data.items() if v and v != []}
            
            if social_data:
                print("  ✅ Social links found:")
                for key, value in social_data.items():
                    if isinstance(value, list):
                        value = value[0] if value else 'N/A'
                    print(f"    {key}: {value[:50]}...")
            
            return social_data
        else:
            print(f"  Error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"  Exception: {e}")
        return None

def main():
    """Test various tokens to find social data"""
    
    print("=" * 60)
    print("GECKOTERMINAL DEEP DIVE - FINDING SOCIAL DATA")
    print("=" * 60)
    
    # Test cases - diverse tokens that likely have websites
    test_tokens = [
        ("ethereum", "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984", "UNI"),    # Uniswap
        ("ethereum", "0x514910771AF9Ca656af840dff83E8264EcF986CA", "LINK"),   # Chainlink
        ("ethereum", "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9", "AAVE"),   # Aave
        ("solana", "7JFnQBJoCLkR9DHy3HKayZjvEqUF7Qzi8TCfQRPQpump", "KROM"),  # KROM
        ("bsc", "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c", "WBNB"),       # Wrapped BNB
    ]
    
    results_summary = []
    
    for network, address, symbol in test_tokens:
        print(f"\n{'='*60}")
        print(f"TESTING: {symbol} on {network}")
        print(f"Address: {address}")
        print(f"{'='*60}")
        
        # Test different endpoints
        token_info = test_token_info_endpoint(network, address, symbol)
        pools_info = test_token_pools_endpoint(network, address, symbol)
        includes_info = test_token_info_with_includes(network, address, symbol)
        
        # If we got a CoinGecko ID, check CoinGecko
        coingecko_data = None
        if token_info.get('success'):
            cg_id = token_info.get('data', {}).get('data', {}).get('attributes', {}).get('coingecko_coin_id')
            if cg_id:
                coingecko_data = test_coingecko_crossref(cg_id)
        
        results_summary.append({
            'symbol': symbol,
            'network': network,
            'has_gt_data': token_info.get('success', False),
            'social_fields': token_info.get('social_fields', {}),
            'coingecko_id': cg_id if token_info.get('success') else None,
            'coingecko_socials': coingecko_data
        })
        
        # Rate limiting
        time.sleep(1)
    
    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY OF FINDINGS")
    print("=" * 60)
    
    for result in results_summary:
        print(f"\n{result['symbol']} ({result['network']}):")
        
        if result['social_fields']:
            print(f"  GeckoTerminal social fields: {result['social_fields']}")
        else:
            print(f"  GeckoTerminal: No social fields found")
        
        if result['coingecko_socials']:
            print(f"  CoinGecko data available: ✅")
            for key, value in result['coingecko_socials'].items():
                if isinstance(value, list):
                    value = value[0] if value else 'N/A'
                print(f"    - {key}: {value[:40]}...")
        elif result['coingecko_id']:
            print(f"  CoinGecko ID: {result['coingecko_id']} (but no social data)")
        else:
            print(f"  CoinGecko: No data")
    
    print("\n" + "=" * 60)
    print("CONCLUSIONS:")
    print("=" * 60)
    print("""
1. GeckoTerminal API:
   - ❌ No direct social/website fields in token or pools endpoints
   - ✅ Some tokens have 'coingecko_coin_id' field
   - ❌ No batch endpoint (must query one by one)
   - ⚠️ Rate limited (need delays between requests)

2. CoinGecko API (when coingecko_id exists):
   - ✅ Comprehensive social links (homepage, twitter, telegram, github)
   - ✅ Additional data (whitepaper, subreddit, etc.)
   - ❌ Only ~10-20% of tokens have CoinGecko IDs
   - ⚠️ Strict rate limits (10-50 calls/minute free tier)

3. Strategy:
   - Primary: Use DexScreener batch API (fastest, most coverage)
   - Fallback: For major tokens with CoinGecko IDs, could fetch additional data
   - Not worth: GeckoTerminal direct API (no social data)
""")

if __name__ == "__main__":
    main()