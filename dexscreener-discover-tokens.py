#!/usr/bin/env python3
"""
DexScreener Token Discovery Script
Discovers various tokens using working endpoints
"""

import requests
import json
from datetime import datetime
import time
from collections import defaultdict

BASE_URL = "https://api.dexscreener.com"

def get_tokens_from_endpoint(endpoint, params=None):
    """Get tokens from an endpoint and extract unique token addresses"""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            tokens = defaultdict(dict)
            
            # Extract from pairs format
            if isinstance(data, dict) and 'pairs' in data:
                for pair in data['pairs']:
                    if 'baseToken' in pair:
                        token_addr = pair['baseToken'].get('address', '')
                        if token_addr:
                            tokens[token_addr] = {
                                'symbol': pair['baseToken'].get('symbol', ''),
                                'name': pair['baseToken'].get('name', ''),
                                'chain': pair.get('chainId', ''),
                                'price': pair.get('priceUsd', ''),
                                'volume24h': pair.get('volume', {}).get('h24', 0),
                                'priceChange24h': pair.get('priceChange', {}).get('h24', 0),
                                'liquidity': pair.get('liquidity', {}).get('usd', 0),
                                'url': pair.get('url', ''),
                                'dexId': pair.get('dexId', '')
                            }
            
            # Extract from token profiles format
            elif isinstance(data, list):
                for item in data:
                    token_addr = item.get('tokenAddress', '')
                    if token_addr:
                        tokens[token_addr] = {
                            'chain': item.get('chainId', ''),
                            'url': item.get('url', ''),
                            'description': item.get('description', ''),
                            'links': item.get('links', [])
                        }
                        
            return tokens
        return {}
        
    except Exception as e:
        print(f"Error fetching {endpoint}: {str(e)}")
        return {}

def discover_all_tokens():
    """Discover tokens from all working endpoints"""
    print("="*80)
    print("DexScreener Token Discovery")
    print(f"Timestamp: {datetime.now()}")
    print("="*80)
    
    all_tokens = defaultdict(dict)
    
    # 1. Get new tokens
    print("\n[1/7] Fetching new tokens...")
    new_tokens = get_tokens_from_endpoint("/latest/dex/tokens/new")
    print(f"Found {len(new_tokens)} unique new tokens")
    all_tokens.update(new_tokens)
    time.sleep(0.5)
    
    # 2. Get trending tokens
    print("\n[2/7] Fetching trending tokens...")
    trending_tokens = get_tokens_from_endpoint("/latest/dex/tokens/trending")
    print(f"Found {len(trending_tokens)} unique trending tokens")
    all_tokens.update(trending_tokens)
    time.sleep(0.5)
    
    # 3. Search for popular meme coins
    print("\n[3/7] Searching for meme coins...")
    meme_searches = ["PEPE", "SHIB", "DOGE", "BONK", "WIF", "FLOKI", "MEME", "WOJAK"]
    for search in meme_searches:
        tokens = get_tokens_from_endpoint("/latest/dex/search", params={"q": search})
        print(f"  {search}: {len(tokens)} tokens found")
        all_tokens.update(tokens)
        time.sleep(0.3)
    
    # 4. Get boosted tokens
    print("\n[4/7] Fetching boosted tokens...")
    boosted_tokens = get_tokens_from_endpoint("/token-boosts/top/v1")
    print(f"Found {len(boosted_tokens)} top boosted tokens")
    all_tokens.update(boosted_tokens)
    time.sleep(0.5)
    
    latest_boosted = get_tokens_from_endpoint("/token-boosts/latest/v1")
    print(f"Found {len(latest_boosted)} latest boosted tokens")
    all_tokens.update(latest_boosted)
    time.sleep(0.5)
    
    # 5. Get token profiles
    print("\n[5/7] Fetching token profiles...")
    profiles = get_tokens_from_endpoint("/token-profiles/latest/v1")
    print(f"Found {len(profiles)} token profiles")
    all_tokens.update(profiles)
    
    # 6. Search for AI/tech tokens
    print("\n[6/7] Searching for AI/tech tokens...")
    tech_searches = ["AI", "GPT", "BOT", "TECH", "CYBER", "NEURAL"]
    for search in tech_searches:
        tokens = get_tokens_from_endpoint("/latest/dex/search", params={"q": search})
        print(f"  {search}: {len(tokens)} tokens found")
        all_tokens.update(tokens)
        time.sleep(0.3)
    
    # 7. Search by chain-specific popular tokens
    print("\n[7/7] Searching chain-specific tokens...")
    chain_searches = ["ETH", "BNB", "SOL", "MATIC", "AVAX"]
    for search in chain_searches:
        tokens = get_tokens_from_endpoint("/latest/dex/search", params={"q": search})
        print(f"  {search}: {len(tokens)} tokens found")
        all_tokens.update(tokens)
        time.sleep(0.3)
    
    return all_tokens

def analyze_tokens(tokens):
    """Analyze discovered tokens"""
    print("\n" + "="*80)
    print("Token Analysis")
    print("="*80)
    
    print(f"\nTotal unique tokens discovered: {len(tokens)}")
    
    # Group by chain
    chains = defaultdict(int)
    for token_data in tokens.values():
        if 'chain' in token_data:
            chains[token_data['chain']] += 1
    
    print("\nTokens by chain:")
    for chain, count in sorted(chains.items(), key=lambda x: x[1], reverse=True):
        if chain:  # Skip empty chains
            print(f"  {chain}: {count}")
    
    # Find high volume tokens
    high_volume = []
    for addr, data in tokens.items():
        if 'volume24h' in data and data['volume24h']:
            try:
                vol = float(data['volume24h'])
                if vol > 100000:  # > $100k volume
                    high_volume.append((addr, data, vol))
            except:
                pass
    
    print(f"\nHigh volume tokens (>$100k 24h volume): {len(high_volume)}")
    high_volume.sort(key=lambda x: x[2], reverse=True)
    
    for i, (addr, data, vol) in enumerate(high_volume[:10]):
        print(f"\n{i+1}. {data.get('symbol', 'Unknown')} ({data.get('name', 'Unknown')})")
        print(f"   Chain: {data.get('chain', 'Unknown')}")
        print(f"   Address: {addr}")
        print(f"   24h Volume: ${vol:,.2f}")
        if data.get('price'):
            print(f"   Price: ${data['price']}")
        if data.get('priceChange24h'):
            print(f"   24h Change: {data['priceChange24h']}%")
        if data.get('url'):
            print(f"   URL: {data['url']}")

def save_tokens(tokens, filename="discovered_tokens.json"):
    """Save discovered tokens to a JSON file"""
    # Convert to serializable format
    output = {}
    for addr, data in tokens.items():
        output[addr] = {k: str(v) if v else "" for k, v in data.items()}
    
    with open(filename, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✅ Saved {len(tokens)} tokens to {filename}")

def main():
    # Discover tokens
    tokens = discover_all_tokens()
    
    # Analyze tokens
    analyze_tokens(tokens)
    
    # Save tokens
    save_tokens(tokens)
    
    print("\n" + "="*80)
    print("Discovery complete!")
    print("="*80)

if __name__ == "__main__":
    main()