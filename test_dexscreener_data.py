#!/usr/bin/env python3
"""
Test DexScreener API to see what data they provide, especially social media
"""
import requests
import json
from datetime import datetime

def test_dexscreener_api():
    """Test DexScreener API endpoints"""
    
    # Test with a known token that should have social data
    # Using KROM token on Solana
    print("=== Testing DexScreener API ===\n")
    
    # Get token pairs for KROM
    url = "https://api.dexscreener.com/latest/dex/tokens/7nWMN3CBdBCKqtBjfDWUYf6qHtdW8B3cq6aVYQLeUAkV"
    
    print(f"Fetching: {url}")
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        
        if data.get('pairs'):
            pair = data['pairs'][0]  # Get first pair
            
            print(f"\n✅ Token: {pair.get('baseToken', {}).get('symbol')} - {pair.get('baseToken', {}).get('name')}")
            print(f"Chain: {pair.get('chainId')}")
            print(f"DEX: {pair.get('dexId')}")
            print(f"Price USD: ${pair.get('priceUsd')}")
            print(f"Liquidity: ${pair.get('liquidity', {}).get('usd')}")
            print(f"FDV: ${pair.get('fdv')}")
            print(f"Market Cap: ${pair.get('marketCap')}")
            
            # Check for info/social data
            info = pair.get('info', {})
            print("\n=== Social Media & Website Data ===")
            
            if info:
                print(f"Image URL: {info.get('imageUrl', 'N/A')}")
                
                websites = info.get('websites', [])
                if websites:
                    print("\nWebsites:")
                    for site in websites:
                        print(f"  - {site.get('url')}")
                else:
                    print("Websites: None")
                    
                socials = info.get('socials', [])
                if socials:
                    print("\nSocial Media:")
                    for social in socials:
                        print(f"  - {social.get('type')}: {social.get('url')}")
                else:
                    print("Social Media: None")
            else:
                print("No info/social data available")
                
            # Show all available fields
            print("\n=== All Available Fields ===")
            print(f"Top-level fields: {list(pair.keys())}")
            
            if pair.get('baseToken'):
                print(f"Base token fields: {list(pair['baseToken'].keys())}")
                
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

def test_batch_tokens():
    """Test getting multiple tokens at once"""
    print("\n\n=== Testing Batch Token Fetch ===\n")
    
    # Multiple token addresses (can query up to 30 at once)
    tokens = [
        "7nWMN3CBdBCKqtBjfDWUYf6qHtdW8B3cq6aVYQLeUAkV",  # KROM
        "DezXAZ8z7PnrnRJjz3wXBoZqqhsf6B3ATE7qJJr8RE",     # BONK
        "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"    # USDC
    ]
    
    # Join addresses with comma
    addresses = ",".join(tokens)
    url = f"https://api.dexscreener.com/latest/dex/tokens/{addresses}"
    
    print(f"Fetching {len(tokens)} tokens in one request...")
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        
        for pair_data in data.get('pairs', []):
            token = pair_data.get('baseToken', {})
            info = pair_data.get('info', {})
            
            has_website = len(info.get('websites', [])) > 0
            has_socials = len(info.get('socials', [])) > 0
            
            print(f"\n{token.get('symbol')}:")
            print(f"  - Has Website: {'✅' if has_website else '❌'}")
            print(f"  - Has Socials: {'✅' if has_socials else '❌'}")
            
            if has_website:
                for site in info.get('websites', []):
                    print(f"  - Website: {site.get('url')}")
                    
            if has_socials:
                for social in info.get('socials', []):
                    print(f"  - {social.get('type')}: {social.get('url')}")
    else:
        print(f"Error: {response.status_code}")

def test_search_api():
    """Test DexScreener search API"""
    print("\n\n=== Testing Search API ===\n")
    
    # Search for tokens
    query = "pump"
    url = f"https://api.dexscreener.com/latest/dex/search/?q={query}"
    
    print(f"Searching for: {query}")
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        pairs = data.get('pairs', [])
        
        print(f"Found {len(pairs)} results")
        
        # Check first 5 results for social data
        for pair in pairs[:5]:
            token = pair.get('baseToken', {})
            info = pair.get('info', {})
            
            has_website = len(info.get('websites', [])) > 0
            has_socials = len(info.get('socials', [])) > 0
            
            print(f"\n{token.get('symbol')} - {token.get('name')}:")
            print(f"  Chain: {pair.get('chainId')}")
            print(f"  Has Website: {'✅' if has_website else '❌'}")
            print(f"  Has Socials: {'✅' if has_socials else '❌'}")
    else:
        print(f"Error: {response.status_code}")

if __name__ == "__main__":
    test_dexscreener_api()
    test_batch_tokens()
    test_search_api()