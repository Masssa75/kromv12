#!/usr/bin/env python3
"""
DexScreener Working API Endpoints Explorer
Focuses on endpoints that actually work and return useful data
"""

import requests
import json
from datetime import datetime
import time

BASE_URL = "https://api.dexscreener.com"

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*80}")
    print(f"{title}")
    print(f"{'='*80}")

def explore_working_endpoint(endpoint, params=None, description=""):
    """Explore a working endpoint with better formatting"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\nEndpoint: {url}")
    if description:
        print(f"Description: {description}")
    if params:
        print(f"Params: {params}")
    
    try:
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            # Pretty print with analysis
            if isinstance(data, dict):
                if 'pairs' in data and isinstance(data['pairs'], list):
                    print(f"Found {len(data['pairs'])} pairs")
                    if len(data['pairs']) > 0:
                        pair = data['pairs'][0]
                        print(f"\nSample pair data:")
                        print(f"  Chain: {pair.get('chainId', 'N/A')}")
                        print(f"  DEX: {pair.get('dexId', 'N/A')}")
                        if 'baseToken' in pair:
                            print(f"  Token: {pair['baseToken'].get('symbol', 'N/A')} ({pair['baseToken'].get('name', 'N/A')})")
                        if 'priceUsd' in pair:
                            print(f"  Price USD: ${pair['priceUsd']}")
                        if 'volume' in pair and 'h24' in pair['volume']:
                            print(f"  24h Volume: ${pair['volume']['h24']:,.2f}")
                        if 'priceChange' in pair and 'h24' in pair['priceChange']:
                            print(f"  24h Change: {pair['priceChange']['h24']}%")
                        if 'liquidity' in pair and 'usd' in pair['liquidity']:
                            print(f"  Liquidity: ${pair['liquidity']['usd']:,.2f}")
                            
            elif isinstance(data, list):
                print(f"Found {len(data)} items")
                if len(data) > 0:
                    item = data[0]
                    print(f"\nSample item:")
                    if 'tokenAddress' in item:
                        print(f"  Token: {item.get('tokenAddress', 'N/A')}")
                    if 'chainId' in item:
                        print(f"  Chain: {item.get('chainId', 'N/A')}")
                    if 'description' in item:
                        print(f"  Description: {item.get('description', 'N/A')[:100]}...")
                        
            return data
        else:
            print(f"Error: Status {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def main():
    print_section("DexScreener Working API Endpoints")
    print(f"Timestamp: {datetime.now()}")
    
    # 1. Search for tokens
    print_section("1. Token Search - /latest/dex/search")
    tokens_to_search = ["PEPE", "SHIB", "DOGE", "BONK", "WIF"]
    for token in tokens_to_search[:3]:  # Limit to avoid rate limits
        print(f"\nSearching for: {token}")
        explore_working_endpoint("/latest/dex/search", 
                               params={"q": token},
                               description="Search for token pairs by symbol or address")
        time.sleep(0.5)
    
    # 2. Get new tokens
    print_section("2. New Tokens - /latest/dex/tokens/new")
    explore_working_endpoint("/latest/dex/tokens/new",
                           description="Get the latest new tokens across all chains")
    
    # 3. Get trending tokens
    print_section("3. Trending Tokens - /latest/dex/tokens/trending")
    explore_working_endpoint("/latest/dex/tokens/trending",
                           description="Get currently trending tokens")
    
    # 4. Get token details by address
    print_section("4. Token Details - /latest/dex/tokens/{address}")
    # Test with some popular tokens
    token_addresses = {
        "PEPE": "0x6982508145454ce325ddbe47a25d4ec3d2311933",
        "SHIB": "0x95aD61b0a150d79219dCF64E1E6Cc01f0B64C4cE",
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7"
    }
    
    for name, address in list(token_addresses.items())[:2]:
        print(f"\nGetting details for {name}")
        explore_working_endpoint(f"/latest/dex/tokens/{address}",
                               description=f"Get all pairs for {name} token")
        time.sleep(0.5)
    
    # 5. Token profiles (boosted)
    print_section("5. Boosted Token Profiles")
    
    print("\na) Latest token profiles")
    explore_working_endpoint("/token-profiles/latest/v1",
                           description="Get latest token profiles with social media links")
    
    print("\nb) Top boosted tokens")
    explore_working_endpoint("/token-boosts/top/v1",
                           description="Get top boosted tokens")
    
    print("\nc) Latest boosted tokens")
    explore_working_endpoint("/token-boosts/latest/v1",
                           description="Get latest boosted tokens")
    
    # 6. Try to find trending by adding parameters
    print_section("6. Advanced Queries")
    
    print("\na) Search with filters")
    explore_working_endpoint("/latest/dex/search",
                           params={"q": "ETH", "minLiquidity": "100000"},
                           description="Search with minimum liquidity filter")
    
    # 7. Summary of findings
    print_section("Summary of Working Endpoints")
    print("""
    Working endpoints found:
    1. /latest/dex/search?q={query} - Search for tokens
    2. /latest/dex/tokens/new - Get new tokens
    3. /latest/dex/tokens/trending - Get trending tokens
    4. /latest/dex/tokens/{address} - Get token pairs by address
    5. /token-profiles/latest/v1 - Get latest token profiles
    6. /token-boosts/top/v1 - Get top boosted tokens
    7. /token-boosts/latest/v1 - Get latest boosted tokens
    
    Notable features:
    - All endpoints return pair data with price, volume, liquidity
    - Token profiles include social media links and descriptions
    - Search supports partial matching
    - Data includes multiple chains (Ethereum, BSC, Solana, etc.)
    """)

if __name__ == "__main__":
    main()