#!/usr/bin/env python3
"""
Token Discovery System for Website Analysis
Provides multiple streams of interesting tokens to analyze
"""

import requests
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os
from dotenv import load_dotenv

load_dotenv()

class TokenDiscoverySystem:
    def __init__(self):
        self.dexscreener_headers = {
            'Accept': 'application/json',
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        
    def get_geckoterminal_trending(self, network: str = "solana", min_liquidity: float = 50000) -> List[Dict]:
        """
        Get trending tokens from GeckoTerminal
        These usually have websites as they're more established
        """
        print(f"\n🔥 Fetching TRENDING tokens from GeckoTerminal ({network})...")
        
        network_map = {
            'solana': 'solana',
            'ethereum': 'eth',
            'base': 'base',
            'arbitrum': 'arbitrum',
            'polygon': 'polygon'
        }
        
        gt_network = network_map.get(network, network)
        tokens = []
        
        try:
            # Get trending pools
            url = f"https://api.geckoterminal.com/api/v2/networks/{gt_network}/trending_pools"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                pools = data.get('data', [])
                
                for pool in pools[:20]:  # Top 20 trending
                    attrs = pool.get('attributes', {})
                    relationships = pool.get('relationships', {})
                    
                    # Extract token info from relationships
                    base_token = relationships.get('base_token', {}).get('data', {})
                    base_token_id = base_token.get('id', '')
                    
                    # Parse token address from ID (format: network_address)
                    token_address = base_token_id.split('_')[-1] if '_' in base_token_id else ''
                    
                    liquidity = float(attrs.get('reserve_in_usd', 0))
                    
                    if liquidity >= min_liquidity:
                        token_data = {
                            'address': token_address or attrs.get('address', ''),
                            'symbol': attrs.get('name', '').split(' / ')[0] if ' / ' in attrs.get('name', '') else '',
                            'name': attrs.get('name', ''),
                            'network': network,
                            'liquidity_usd': liquidity,
                            'volume_24h': float(attrs.get('volume_usd', {}).get('h24', 0)),
                            'price_change_24h': float(attrs.get('price_change_percentage', {}).get('h24', 0)),
                            'pool_created_at': attrs.get('pool_created_at', ''),
                            'source': 'geckoterminal_trending',
                            'reason': 'Trending on GeckoTerminal',
                            'likelihood_has_website': 'HIGH'  # Trending tokens often have websites
                        }
                        tokens.append(token_data)
                
                print(f"  ✅ Found {len(tokens)} trending tokens with liquidity > ${min_liquidity:,.0f}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        return tokens
    
    def get_geckoterminal_new_gems(self, network: str = "solana", hours: int = 24) -> List[Dict]:
        """
        Get new tokens that show strong early metrics
        Filter for ones likely to have websites
        """
        print(f"\n💎 Fetching NEW GEMS from GeckoTerminal (last {hours}h)...")
        
        network_map = {
            'solana': 'solana',
            'ethereum': 'eth',
            'base': 'base'
        }
        
        gt_network = network_map.get(network, network)
        tokens = []
        
        try:
            # Get new pools
            url = f"https://api.geckoterminal.com/api/v2/networks/{gt_network}/new_pools?page=1"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                pools = data.get('data', [])
                
                cutoff_time = datetime.now() - timedelta(hours=hours)
                
                for pool in pools:
                    attrs = pool.get('attributes', {})
                    
                    # Parse creation time
                    created_str = attrs.get('pool_created_at', '')
                    if created_str:
                        # Remove timezone info for comparison
                        created = datetime.fromisoformat(created_str.replace('Z', '+00:00')).replace(tzinfo=None)
                        
                        if created < cutoff_time:
                            continue
                    
                    # Look for high-quality new tokens
                    liquidity = float(attrs.get('reserve_in_usd', 0))
                    volume = float(attrs.get('volume_usd', {}).get('h24', 0))
                    txns = int(attrs.get('transactions', {}).get('h24', {}).get('buys', 0))
                    
                    # Quality filters - tokens likely to have websites
                    if liquidity > 100000 and volume > 50000 and txns > 100:
                        token_data = {
                            'address': attrs.get('base_token_address', ''),
                            'symbol': attrs.get('base_token_symbol', ''),
                            'name': attrs.get('base_token_name', ''),
                            'network': network,
                            'liquidity_usd': liquidity,
                            'volume_24h': volume,
                            'transactions_24h': txns,
                            'pool_created_at': created_str,
                            'age_hours': (datetime.now() - created.replace(tzinfo=None)).total_seconds() / 3600,
                            'source': 'geckoterminal_new_gems',
                            'reason': f'New token with ${liquidity/1000:.0f}k liquidity, {txns} txns',
                            'likelihood_has_website': 'MEDIUM'  # Quality new tokens might have websites
                        }
                        tokens.append(token_data)
                
                print(f"  ✅ Found {len(tokens)} quality new tokens")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        return tokens
    
    def get_dexscreener_boosted(self) -> List[Dict]:
        """
        Get BOOSTED tokens from DexScreener
        These are promoted/paid tokens - very likely to have websites
        """
        print(f"\n🚀 Fetching BOOSTED tokens from DexScreener...")
        
        tokens = []
        
        try:
            url = "https://api.dexscreener.com/latest/dex/tokens/boosted"
            response = requests.get(url, headers=self.dexscreener_headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Handle both list and dict responses
                token_list = data if isinstance(data, list) else data.get('tokens', [])
                
                for token in token_list[:30]:  # Top 30 boosted
                    # Get the best pair (highest liquidity)
                    pairs = token.get('pairs', []) if isinstance(token, dict) else []
                    if not pairs:
                        continue
                    
                    best_pair = max(pairs, 
                                  key=lambda x: x.get('liquidity', {}).get('usd', 0) if x else 0)
                    
                    if best_pair:
                        token_data = {
                            'address': token.get('tokenAddress', ''),
                            'symbol': best_pair.get('baseToken', {}).get('symbol', ''),
                            'name': best_pair.get('baseToken', {}).get('name', ''),
                            'network': best_pair.get('chainId', ''),
                            'liquidity_usd': best_pair.get('liquidity', {}).get('usd', 0),
                            'volume_24h': best_pair.get('volume', {}).get('h24', 0),
                            'price_change_24h': best_pair.get('priceChange', {}).get('h24', 0),
                            'website': best_pair.get('info', {}).get('websites', [None])[0],
                            'twitter': best_pair.get('info', {}).get('socials', [{}])[0].get('url') if best_pair.get('info', {}).get('socials') else None,
                            'source': 'dexscreener_boosted',
                            'reason': 'Paid promotion (boosted)',
                            'likelihood_has_website': 'VERY HIGH'  # Boosted tokens almost always have websites
                        }
                        
                        # Only include if it already has website info
                        if token_data['website'] or token_data['twitter']:
                            tokens.append(token_data)
                
                print(f"  ✅ Found {len(tokens)} boosted tokens with social info")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        return tokens
    
    def get_dexscreener_top_gainers(self, min_liquidity: float = 100000) -> List[Dict]:
        """
        Get top gainers from DexScreener
        Established tokens with momentum - likely to have websites
        """
        print(f"\n📈 Fetching TOP GAINERS from DexScreener...")
        
        tokens = []
        
        try:
            # Try multiple sorting options
            sort_options = ['priceChange', 'volume', 'liquidity']
            
            for sort in sort_options[:1]:  # Just use price change for now
                url = f"https://api.dexscreener.com/latest/dex/tokens/top?sort={sort}"
                response = requests.get(url, headers=self.dexscreener_headers, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Handle both list and dict responses
                    token_list = data if isinstance(data, list) else data.get('tokens', [])
                    
                    for token in token_list[:20]:  # Top 20
                        # Get the best pair
                        pairs = token.get('pairs', []) if isinstance(token, dict) else []
                        if not pairs:
                            continue
                        
                        best_pair = max(pairs, 
                                      key=lambda x: x.get('liquidity', {}).get('usd', 0) if x else 0)
                        
                        if best_pair and best_pair.get('liquidity', {}).get('usd', 0) >= min_liquidity:
                            token_data = {
                                'address': token.get('tokenAddress', ''),
                                'symbol': best_pair.get('baseToken', {}).get('symbol', ''),
                                'name': best_pair.get('baseToken', {}).get('name', ''),
                                'network': best_pair.get('chainId', ''),
                                'liquidity_usd': best_pair.get('liquidity', {}).get('usd', 0),
                                'volume_24h': best_pair.get('volume', {}).get('h24', 0),
                                'price_change_24h': best_pair.get('priceChange', {}).get('h24', 0),
                                'website': best_pair.get('info', {}).get('websites', [None])[0],
                                'twitter': best_pair.get('info', {}).get('socials', [{}])[0].get('url') if best_pair.get('info', {}).get('socials') else None,
                                'source': 'dexscreener_top_gainers',
                                'reason': f'Top gainer: {best_pair.get("priceChange", {}).get("h24", 0):.1f}% in 24h',
                                'likelihood_has_website': 'HIGH'
                            }
                            tokens.append(token_data)
            
            print(f"  ✅ Found {len(tokens)} top gainers with liquidity > ${min_liquidity:,.0f}")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        return tokens
    
    def filter_tokens_with_potential_websites(self, tokens: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Separate tokens into those with websites and those likely to have websites
        """
        has_website = []
        likely_has_website = []
        
        for token in tokens:
            if token.get('website'):
                has_website.append(token)
            elif token.get('likelihood_has_website') in ['HIGH', 'VERY HIGH']:
                likely_has_website.append(token)
        
        return has_website, likely_has_website
    
    def get_comprehensive_token_stream(self) -> Dict[str, List[Dict]]:
        """
        Get tokens from all sources, organized by likelihood of having websites
        """
        print("\n" + "="*60)
        print("🔍 COMPREHENSIVE TOKEN DISCOVERY")
        print("="*60)
        
        all_tokens = []
        
        # 1. DexScreener Boosted (highest likelihood of websites)
        boosted = self.get_dexscreener_boosted()
        all_tokens.extend(boosted)
        time.sleep(1)
        
        # 2. DexScreener Top Gainers
        gainers = self.get_dexscreener_top_gainers()
        all_tokens.extend(gainers)
        time.sleep(1)
        
        # 3. GeckoTerminal Trending
        trending = self.get_geckoterminal_trending()
        all_tokens.extend(trending)
        time.sleep(1)
        
        # 4. GeckoTerminal New Gems
        gems = self.get_geckoterminal_new_gems()
        all_tokens.extend(gems)
        
        # Deduplicate by address
        unique_tokens = {}
        for token in all_tokens:
            if token['address'] not in unique_tokens:
                unique_tokens[token['address']] = token
        
        # Categorize
        result = {
            'has_website': [],
            'very_likely': [],
            'likely': [],
            'maybe': [],
            'all': list(unique_tokens.values())
        }
        
        for token in unique_tokens.values():
            if token.get('website'):
                result['has_website'].append(token)
            elif token.get('likelihood_has_website') == 'VERY HIGH':
                result['very_likely'].append(token)
            elif token.get('likelihood_has_website') == 'HIGH':
                result['likely'].append(token)
            else:
                result['maybe'].append(token)
        
        # Summary
        print("\n" + "="*60)
        print("📊 DISCOVERY SUMMARY")
        print("="*60)
        print(f"✅ Tokens WITH websites: {len(result['has_website'])}")
        print(f"🟢 VERY LIKELY to have websites: {len(result['very_likely'])}")
        print(f"🟡 LIKELY to have websites: {len(result['likely'])}")
        print(f"🔵 MAYBE have websites: {len(result['maybe'])}")
        print(f"📦 TOTAL unique tokens: {len(result['all'])}")
        
        return result

def main():
    """Test the discovery system"""
    discovery = TokenDiscoverySystem()
    
    # Get comprehensive token stream
    tokens = discovery.get_comprehensive_token_stream()
    
    # Show some examples
    print("\n" + "="*60)
    print("🌟 SAMPLE TOKENS FOR WEBSITE ANALYSIS")
    print("="*60)
    
    # Priority 1: Tokens that already have websites
    if tokens['has_website']:
        print("\n🎯 PRIORITY 1: Tokens WITH websites")
        for token in tokens['has_website'][:5]:
            print(f"\n  {token['symbol']} ({token['network']})")
            print(f"  Address: {token['address'][:20]}...")
            print(f"  Website: {token.get('website', 'N/A')}")
            print(f"  Source: {token['source']}")
            print(f"  Reason: {token['reason']}")
    
    # Priority 2: Boosted/promoted tokens
    if tokens['very_likely']:
        print("\n🎯 PRIORITY 2: Tokens VERY LIKELY to have websites")
        for token in tokens['very_likely'][:5]:
            print(f"\n  {token['symbol']} ({token['network']})")
            print(f"  Liquidity: ${token.get('liquidity_usd', 0):,.0f}")
            print(f"  Source: {token['source']}")
            print(f"  Reason: {token['reason']}")
    
    # Priority 3: Trending established tokens
    if tokens['likely']:
        print("\n🎯 PRIORITY 3: Tokens LIKELY to have websites")
        for token in tokens['likely'][:5]:
            print(f"\n  {token['symbol']} ({token['network']})")
            print(f"  Volume 24h: ${token.get('volume_24h', 0):,.0f}")
            print(f"  Source: {token['source']}")
            print(f"  Reason: {token['reason']}")
    
    # Save results
    output_file = 'token_discovery_results.json'
    with open(output_file, 'w') as f:
        json.dump(tokens, f, indent=2)
    
    print(f"\n💾 Results saved to {output_file}")
    
    print("\n" + "="*60)
    print("🎯 RECOMMENDATION FOR TOKEN STREAM")
    print("="*60)
    print("""
1. IMMEDIATE: Use DexScreener Boosted tokens
   - Already have website URLs in API response
   - Paid promotions = serious projects
   - ~20-30 tokens available at any time
   
2. HIGH VALUE: DexScreener Top Gainers + GeckoTerminal Trending
   - Established tokens with momentum
   - High likelihood of having websites
   - ~40-50 tokens per hour
   
3. DISCOVERY: GeckoTerminal New Gems (filtered)
   - New tokens with >$100k liquidity
   - Some will have websites prepared at launch
   - ~10-20 quality tokens per hour
   
4. CONTINUOUS: Set up monitoring that:
   - Polls every 5-10 minutes
   - Deduplicates tokens
   - Checks if website exists (HTTP HEAD request)
   - Queues tokens with websites for analysis
    """)

if __name__ == "__main__":
    main()