#!/usr/bin/env python3
"""
DexScreener API Explorer
Explores various DexScreener API endpoints to discover available data
"""

import requests
import json
from datetime import datetime
import time

# Base URL for DexScreener API
BASE_URL = "https://api.dexscreener.com"

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")

def explore_endpoint(endpoint, params=None, method="GET", data=None):
    """Explore a single endpoint and print results"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n[{method}] {url}")
    if params:
        print(f"Params: {params}")
    
    try:
        if method == "GET":
            response = requests.get(url, params=params)
        elif method == "POST":
            response = requests.post(url, json=data)
        else:
            print(f"Unsupported method: {method}")
            return None
            
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response Type: {type(data)}")
            
            # Handle different response types
            if isinstance(data, dict):
                print(f"Keys: {list(data.keys())}")
                
                # Show sample data for lists
                for key, value in data.items():
                    if isinstance(value, list) and len(value) > 0:
                        print(f"\n{key} (showing first item):")
                        print(json.dumps(value[0], indent=2)[:500] + "...")
                    elif isinstance(value, (str, int, float, bool)):
                        print(f"{key}: {value}")
                        
            elif isinstance(data, list):
                print(f"List Length: {len(data)}")
                if len(data) > 0:
                    print("First item:")
                    print(json.dumps(data[0], indent=2)[:500] + "...")
                    
            return data
        else:
            print(f"Error Response: {response.text[:200]}")
            return None
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return None

def main():
    """Main exploration function"""
    
    print_section("DexScreener API Explorer")
    print(f"Timestamp: {datetime.now()}")
    
    # Test basic endpoints
    print_section("1. Testing /latest/dex/tokens/new")
    explore_endpoint("/latest/dex/tokens/new")
    
    print_section("2. Testing /latest/dex/search")
    # Try searching for popular tokens
    explore_endpoint("/latest/dex/search", params={"q": "PEPE"})
    
    print_section("3. Testing /orders/v1/")
    explore_endpoint("/orders/v1/")
    
    print_section("4. Testing /token-profiles/latest/v1")
    explore_endpoint("/token-profiles/latest/v1")
    
    print_section("5. Testing /latest/dex/pairs/{chain}")
    # Try different chains
    chains = ["ethereum", "bsc", "polygon", "arbitrum", "solana"]
    for chain in chains[:2]:  # Test first 2 to avoid rate limits
        print(f"\nTesting chain: {chain}")
        explore_endpoint(f"/latest/dex/pairs/{chain}")
        time.sleep(0.5)  # Small delay to avoid rate limiting
    
    print_section("6. Testing /latest/dex/tokens/{tokenAddress}")
    # Try a well-known token (USDC on Ethereum)
    explore_endpoint("/latest/dex/tokens/0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48")
    
    print_section("7. Testing trending/hot tokens endpoints")
    # Try various trending endpoints
    trending_endpoints = [
        "/dex/screener/pairs/solana/trending",
        "/token-boosts/latest/v1",
        "/token-boosts/top/v1",
        "/latest/dex/tokens/trending",
        "/v1/trending",
        "/screener/pairs/trending"
    ]
    
    for endpoint in trending_endpoints:
        explore_endpoint(endpoint)
        time.sleep(0.5)
    
    print_section("8. Testing token profile by address")
    # Example: PEPE token
    explore_endpoint("/token-profiles/latest/v1", params={"address": "0x6982508145454ce325ddbe47a25d4ec3d2311933"})
    
    print_section("9. Testing boosted tokens")
    explore_endpoint("/token-boosts/active/1")
    
    print_section("10. Testing new pairs")
    explore_endpoint("/latest/dex/pairs/new/1")
    
    print_section("11. Testing gainers/losers")
    explore_endpoint("/gainers-losers/latest/1h")
    
    print_section("Summary")
    print("Exploration complete! Check the output above for working endpoints.")

if __name__ == "__main__":
    main()