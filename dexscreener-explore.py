#!/usr/bin/env python3
"""
DexScreener API Explorer - See what data is available
"""
import requests
import json
from datetime import datetime

def explore_dexscreener():
    """Fetch and analyze available DexScreener data"""
    
    print("🔍 Exploring DexScreener API...")
    print("=" * 60)
    
    # 1. Get latest token profiles
    print("\n1. LATEST TOKEN PROFILES:")
    try:
        response = requests.get("https://api.dexscreener.com/token-profiles/latest/v1")
        if response.status_code == 200:
            profiles = response.json()
            print(f"Found {len(profiles)} token profiles")
            
            # Show first 3 as examples
            for i, profile in enumerate(profiles[:3]):
                print(f"\nToken {i+1}:")
                print(f"  - URL: {profile.get('url', 'N/A')}")
                print(f"  - Chain ID: {profile.get('chainId', 'N/A')}")
                print(f"  - Token Address: {profile.get('tokenAddress', 'N/A')}")
                if 'description' in profile:
                    desc = profile['description'][:100] + "..." if len(profile.get('description', '')) > 100 else profile.get('description', '')
                    print(f"  - Description: {desc}")
    except Exception as e:
        print(f"Error fetching profiles: {e}")
    
    # 2. Get latest boosted tokens
    print("\n\n2. LATEST BOOSTED TOKENS:")
    try:
        response = requests.get("https://api.dexscreener.com/token-boosts/latest/v1")
        if response.status_code == 200:
            boosts = response.json()
            print(f"Found {len(boosts)} boosted tokens")
            
            for i, boost in enumerate(boosts[:3]):
                print(f"\nBoosted Token {i+1}:")
                print(f"  - URL: {boost.get('url', 'N/A')}")
                print(f"  - Chain: {boost.get('chainId', 'N/A')}")
                print(f"  - Token Address: {boost.get('tokenAddress', 'N/A')}")
                print(f"  - Amount: {boost.get('amount', 'N/A')}")
                print(f"  - Total Amount: {boost.get('totalAmount', 'N/A')}")
    except Exception as e:
        print(f"Error fetching boosts: {e}")
    
    # 3. Try to get specific token pair data (example: a popular token)
    print("\n\n3. EXAMPLE TOKEN PAIR DATA:")
    # Let's try PEPE on Ethereum as an example
    try:
        response = requests.get("https://api.dexscreener.com/latest/dex/tokens/0x6982508145454ce325ddbe47a25d4ec3d2311933")
        if response.status_code == 200:
            data = response.json()
            if 'pairs' in data and len(data['pairs']) > 0:
                pair = data['pairs'][0]  # Get most liquid pair
                print(f"\nExample: {pair.get('baseToken', {}).get('symbol', 'N/A')} on {pair.get('chainId', 'N/A')}")
                print(f"  - Price: ${pair.get('priceUsd', 'N/A')}")
                print(f"  - Liquidity: ${pair.get('liquidity', {}).get('usd', 'N/A')}")
                print(f"  - 24h Volume: ${pair.get('volume', {}).get('h24', 'N/A')}")
                print(f"  - 24h Buys: {pair.get('txns', {}).get('h24', {}).get('buys', 'N/A')}")
                print(f"  - 24h Sells: {pair.get('txns', {}).get('h24', {}).get('sells', 'N/A')}")
                print(f"  - Price Change 24h: {pair.get('priceChange', {}).get('h24', 'N/A')}%")
                print(f"  - Created: {pair.get('pairCreatedAt', 'N/A')}")
    except Exception as e:
        print(f"Error fetching pair data: {e}")
    
    # 4. Search for new pairs
    print("\n\n4. SEARCH CAPABILITIES:")
    try:
        # Search for recent USDT pairs
        response = requests.get("https://api.dexscreener.com/latest/dex/search?q=USDT")
        if response.status_code == 200:
            data = response.json()
            if 'pairs' in data:
                print(f"Found {len(data['pairs'])} USDT pairs")
                
                # Find newest pairs
                newest_pairs = sorted(data['pairs'], 
                                    key=lambda x: x.get('pairCreatedAt', 0) if x.get('pairCreatedAt') else 0, 
                                    reverse=True)[:3]
                
                for i, pair in enumerate(newest_pairs):
                    created_at = pair.get('pairCreatedAt')
                    if created_at:
                        created_time = datetime.fromtimestamp(created_at / 1000)
                        age = datetime.now() - created_time
                        hours_old = age.total_seconds() / 3600
                        
                        print(f"\nNew Pair {i+1}: {pair.get('baseToken', {}).get('symbol', 'N/A')}")
                        print(f"  - Age: {hours_old:.1f} hours")
                        print(f"  - Liquidity: ${pair.get('liquidity', {}).get('usd', 0):,.0f}")
                        print(f"  - Volume: ${pair.get('volume', {}).get('h24', 0):,.0f}")
    except Exception as e:
        print(f"Error searching: {e}")

if __name__ == "__main__":
    explore_dexscreener()