#!/usr/bin/env python3
"""
Compare trending tokens from GeckoTerminal and DexScreener APIs
to see if they provide better quality tokens than new_pools
"""
import requests
import json
from datetime import datetime
import time

def test_geckoterminal_trending():
    """Test GeckoTerminal trending pools across different networks"""
    print("=" * 80)
    print("GECKOTERMINAL TRENDING POOLS")
    print("=" * 80)
    
    networks = ['solana', 'eth', 'base', 'bsc', 'arbitrum', 'polygon']
    all_trending = []
    
    for network in networks:
        print(f"\n📊 Trending on {network.upper()}:")
        print("-" * 40)
        
        url = f"https://api.geckoterminal.com/api/v2/networks/{network}/trending_pools"
        
        try:
            response = requests.get(url, headers={'Accept': 'application/json'})
            
            if response.status_code == 200:
                data = response.json()
                pools = data.get('data', [])[:5]  # Top 5 trending
                
                for pool in pools:
                    attrs = pool.get('attributes', {})
                    relationships = pool.get('relationships', {})
                    
                    # Get base token info
                    base_token = relationships.get('base_token', {}).get('data', {})
                    token_id = base_token.get('id', '').split('_')[-1]
                    
                    name = attrs.get('name', 'Unknown')
                    symbol = name.split(' / ')[0] if ' / ' in name else name
                    liquidity = float(attrs.get('reserve_in_usd', 0))
                    volume_24h = float(attrs.get('volume_usd', {}).get('h24', 0))
                    price_change = attrs.get('price_change_percentage', {}).get('h24', 0)
                    
                    print(f"  • {symbol:12} | Liq: ${liquidity:,.0f} | Vol24h: ${volume_24h:,.0f} | 24h: {price_change}%")
                    
                    all_trending.append({
                        'network': network,
                        'symbol': symbol,
                        'liquidity': liquidity,
                        'volume_24h': volume_24h,
                        'token_address': token_id
                    })
            else:
                print(f"  Error: {response.status_code}")
                
        except Exception as e:
            print(f"  Error fetching {network}: {str(e)}")
        
        time.sleep(2)  # Rate limit respect
    
    return all_trending

def test_dexscreener_boosted():
    """Test DexScreener top boosted tokens"""
    print("\n" + "=" * 80)
    print("DEXSCREENER TOP BOOSTED TOKENS")
    print("=" * 80)
    
    url = "https://api.dexscreener.com/token-boosts/top/v1"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            
            # Parse the response - it returns an array of boosted tokens
            boosted_tokens = data[:10] if isinstance(data, list) else []
            
            print(f"\n🚀 Top {len(boosted_tokens)} Boosted Tokens:")
            print("-" * 40)
            
            for token in boosted_tokens:
                # The structure might vary, let's see what we get
                print(f"Token data: {json.dumps(token, indent=2)[:200]}...")
                
        else:
            print(f"Error: {response.status_code}")
            print(response.text[:500])
            
    except Exception as e:
        print(f"Error: {str(e)}")

def test_dexscreener_search_trending():
    """Use DexScreener search to find trending tokens"""
    print("\n" + "=" * 80)
    print("DEXSCREENER SEARCH (Finding Hot Tokens)")
    print("=" * 80)
    
    # Search for tokens sorted by different criteria
    search_queries = [
        ("", "h24Volume"),  # Top by 24h volume
        ("", "liquidity"),  # Top by liquidity
        ("", "h6"),         # Top gainers 6h
    ]
    
    for query, sort in search_queries:
        print(f"\n🔍 Sorted by: {sort}")
        print("-" * 40)
        
        url = f"https://api.dexscreener.com/latest/dex/search/?q={query}"
        
        try:
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                pairs = data.get('pairs', [])[:5]  # Top 5
                
                for pair in pairs:
                    token = pair.get('baseToken', {})
                    info = pair.get('info', {})
                    
                    symbol = token.get('symbol', 'Unknown')
                    name = token.get('name', '')
                    chain = pair.get('chainId', '')
                    liquidity = pair.get('liquidity', {}).get('usd', 0)
                    volume_24h = pair.get('volume', {}).get('h24', 0)
                    price_change = pair.get('priceChange', {}).get('h24', 0)
                    
                    # Check for social data
                    has_website = len(info.get('websites', [])) > 0
                    has_socials = len(info.get('socials', [])) > 0
                    
                    social_indicator = ""
                    if has_website and has_socials:
                        social_indicator = "🌐📱"
                    elif has_website:
                        social_indicator = "🌐"
                    elif has_socials:
                        social_indicator = "📱"
                    
                    print(f"  • {symbol:10} ({chain:8}) | Liq: ${liquidity:,.0f} | Vol: ${volume_24h:,.0f} | 24h: {price_change:+.1f}% {social_indicator}")
                    
                    if has_website:
                        for site in info.get('websites', []):
                            print(f"    └─ Website: {site.get('url')}")
                            
            else:
                print(f"Error: {response.status_code}")
                
        except Exception as e:
            print(f"Error: {str(e)}")
        
        time.sleep(1)

def compare_with_new_pools():
    """Compare trending tokens with new_pools to see quality difference"""
    print("\n" + "=" * 80)
    print("COMPARISON: NEW POOLS vs TRENDING")
    print("=" * 80)
    
    # Get some new pools from Solana (most active)
    print("\n📈 NEW POOLS (Solana):")
    print("-" * 40)
    
    url = "https://api.geckoterminal.com/api/v2/networks/solana/new_pools"
    
    try:
        response = requests.get(url, headers={'Accept': 'application/json'})
        
        if response.status_code == 200:
            data = response.json()
            pools = data.get('data', [])[:10]
            
            stats = {
                'total': len(pools),
                'with_liquidity': 0,
                'above_1k': 0,
                'above_10k': 0,
                'above_100k': 0
            }
            
            for pool in pools:
                attrs = pool.get('attributes', {})
                name = attrs.get('name', 'Unknown')
                symbol = name.split(' / ')[0] if ' / ' in name else name
                liquidity = float(attrs.get('reserve_in_usd', 0))
                created_at = attrs.get('pool_created_at', '')
                
                if liquidity > 0:
                    stats['with_liquidity'] += 1
                if liquidity > 1000:
                    stats['above_1k'] += 1
                if liquidity > 10000:
                    stats['above_10k'] += 1
                if liquidity > 100000:
                    stats['above_100k'] += 1
                
                print(f"  • {symbol:12} | Liq: ${liquidity:,.0f} | Created: {created_at[:19]}")
            
            print(f"\n📊 New Pools Stats:")
            print(f"  - With liquidity: {stats['with_liquidity']}/{stats['total']}")
            print(f"  - Above $1K: {stats['above_1k']}")
            print(f"  - Above $10K: {stats['above_10k']}")
            print(f"  - Above $100K: {stats['above_100k']}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

def analyze_token_with_dexscreener(addresses):
    """Get detailed info including social data for tokens"""
    print("\n" + "=" * 80)
    print("CHECKING SOCIAL DATA FOR TRENDING TOKENS")
    print("=" * 80)
    
    # Take first 10 addresses and batch query them
    batch_addresses = addresses[:10]
    
    if not batch_addresses:
        print("No addresses to check")
        return
    
    url = f"https://api.dexscreener.com/latest/dex/tokens/{','.join(batch_addresses)}"
    
    try:
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            pairs = data.get('pairs', [])
            
            # Group by unique token
            unique_tokens = {}
            for pair in pairs:
                token = pair.get('baseToken', {})
                token_addr = token.get('address')
                if token_addr and token_addr not in unique_tokens:
                    unique_tokens[token_addr] = {
                        'symbol': token.get('symbol'),
                        'name': token.get('name'),
                        'info': pair.get('info', {}),
                        'liquidity': pair.get('liquidity', {}).get('usd', 0)
                    }
            
            stats = {
                'total': len(unique_tokens),
                'with_website': 0,
                'with_socials': 0,
                'with_both': 0
            }
            
            print(f"\n🔍 Analyzed {len(unique_tokens)} trending tokens:")
            print("-" * 40)
            
            for addr, token_data in unique_tokens.items():
                info = token_data['info']
                has_website = len(info.get('websites', [])) > 0
                has_socials = len(info.get('socials', [])) > 0
                
                if has_website:
                    stats['with_website'] += 1
                if has_socials:
                    stats['with_socials'] += 1
                if has_website and has_socials:
                    stats['with_both'] += 1
                
                if has_website or has_socials:
                    print(f"\n  {token_data['symbol']} - {token_data['name']}")
                    if has_website:
                        for site in info.get('websites', []):
                            print(f"    🌐 {site.get('url')}")
                    if has_socials:
                        for social in info.get('socials', []):
                            print(f"    📱 {social.get('type')}: {social.get('url')}")
            
            print(f"\n📊 Social Data Stats for Trending Tokens:")
            print(f"  - With website: {stats['with_website']}/{stats['total']} ({stats['with_website']*100/stats['total']:.1f}%)")
            print(f"  - With socials: {stats['with_socials']}/{stats['total']} ({stats['with_socials']*100/stats['total']:.1f}%)")
            print(f"  - With both: {stats['with_both']}/{stats['total']} ({stats['with_both']*100/stats['total']:.1f}%)")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    print("\n🔍 TESTING TRENDING TOKEN DISCOVERY APIS")
    print("=" * 80)
    print("Comparing GeckoTerminal and DexScreener for finding quality tokens")
    print("=" * 80)
    
    # Test GeckoTerminal trending
    trending_tokens = test_geckoterminal_trending()
    
    # Test DexScreener boosted
    test_dexscreener_boosted()
    
    # Test DexScreener search
    test_dexscreener_search_trending()
    
    # Compare with new pools
    compare_with_new_pools()
    
    # Analyze trending tokens for social data
    if trending_tokens:
        addresses = [t['token_address'] for t in trending_tokens if t['token_address']]
        analyze_token_with_dexscreener(addresses)
    
    print("\n" + "=" * 80)
    print("✅ ANALYSIS COMPLETE")
    print("=" * 80)