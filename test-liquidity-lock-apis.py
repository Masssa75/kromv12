#!/usr/bin/env python3
"""Test DexScreener and GeckoTerminal APIs for liquidity lock information"""
import requests
import json
import os

# Get API keys
GECKO_API_KEY = os.getenv("GECKO_TERMINAL_API_KEY", "CG-rNYcUB85FxH1tZqqRmU5H8eY")

# Test tokens with known liquidity status
test_tokens = [
    {
        "name": "PEPE", 
        "network": "ethereum",
        "address": "0x6982508145454ce325ddbe47a25d4ec3d2311933",
        "pool": "0xa43fe16908251ee70ef74718545e4fe6c5ccec9f"  # PEPE/WETH Uniswap V2
    },
    {
        "name": "SHIB",
        "network": "ethereum", 
        "address": "0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce",
        "pool": "0x811beed0119b4afce20d2583eb608c6f7af1954f"  # SHIB/WETH
    }
]

print("=" * 80)
print("Testing DexScreener API for Liquidity Lock Info")
print("=" * 80)

# DexScreener doesn't require API key
for token in test_tokens:
    print(f"\n{token['name']} ({token['network']})")
    print(f"Contract: {token['address']}")
    
    # DexScreener pair endpoint
    dex_url = f"https://api.dexscreener.com/latest/dex/pairs/{token['network']}/{token['pool']}"
    
    try:
        response = requests.get(dex_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'pair' in data:
                pair = data['pair']
                print(f"\nDexScreener Pair Data:")
                print(f"  DEX: {pair.get('dexId', 'N/A')}")
                print(f"  Price USD: ${pair.get('priceUsd', 'N/A')}")
                print(f"  Liquidity USD: ${pair.get('liquidity', {}).get('usd', 'N/A'):,.2f}")
                print(f"  FDV: ${pair.get('fdv', 'N/A'):,.2f}" if pair.get('fdv') else "  FDV: N/A")
                
                # Check for liquidity lock info
                print(f"\n  Liquidity Lock Info:")
                if 'info' in pair:
                    info = pair['info']
                    print(f"    Warnings: {info.get('warnings', [])}")
                    print(f"    Image URL: {'Yes' if info.get('imageUrl') else 'No'}")
                    print(f"    Websites: {info.get('websites', [])}")
                    print(f"    Socials: {list(info.get('socials', {}).keys())}")
                else:
                    print("    No additional info available")
                    
                # Check txns for liquidity events
                if 'txns' in pair:
                    print(f"    Recent txns: {pair['txns'].get('h24', {})}")
            else:
                print(f"  No pair data found")
        else:
            print(f"  Error: {response.status_code}")
    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "=" * 80)
print("Testing GeckoTerminal API for Liquidity Lock Info")
print("=" * 80)

headers = {"x-cg-pro-api-key": GECKO_API_KEY}

for token in test_tokens:
    print(f"\n{token['name']} ({token['network']})")
    
    # GeckoTerminal pool endpoint
    gecko_url = f"https://pro-api.coingecko.com/api/v3/onchain/networks/{token['network']}/pools/{token['pool']}"
    
    try:
        response = requests.get(gecko_url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                pool_data = data['data']
                attrs = pool_data.get('attributes', {})
                
                print(f"\nGeckoTerminal Pool Data:")
                print(f"  Name: {attrs.get('name', 'N/A')}")
                print(f"  Price USD: ${attrs.get('base_token_price_usd', 'N/A')}")
                print(f"  Reserve USD: ${float(attrs.get('reserve_in_usd', 0)):,.2f}")
                print(f"  Pool Created: {attrs.get('pool_created_at', 'N/A')}")
                
                # Look for liquidity lock info
                print(f"\n  Pool Info:")
                print(f"    Address: {attrs.get('address', 'N/A')}")
                
                # Check relationships for additional info
                if 'relationships' in pool_data:
                    print(f"    Relationships: {list(pool_data['relationships'].keys())}")
                
                # Check if there's lock info in the pool data
                for key, value in attrs.items():
                    if 'lock' in key.lower() or 'locked' in key.lower():
                        print(f"    {key}: {value}")
                        
        else:
            print(f"  Error: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "=" * 80)
print("Testing GeckoTerminal Token Info Endpoint")
print("=" * 80)

# Also try the token info endpoint which might have more details
for token in test_tokens:
    print(f"\n{token['name']} Token Info")
    
    token_url = f"https://pro-api.coingecko.com/api/v3/onchain/networks/{token['network']}/tokens/{token['address']}"
    
    try:
        response = requests.get(token_url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data:
                token_data = data['data']
                attrs = token_data.get('attributes', {})
                
                print(f"  Total Supply: {attrs.get('total_supply', 'N/A')}")
                print(f"  Decimals: {attrs.get('decimals', 'N/A')}")
                
                # Check for any security/audit info
                for key, value in attrs.items():
                    if any(word in key.lower() for word in ['lock', 'security', 'audit', 'burn', 'renounce']):
                        print(f"  {key}: {value}")
                        
                # Check top pools
                if 'relationships' in token_data and 'top_pools' in token_data['relationships']:
                    print(f"  Has top pools data: Yes")
                    
        else:
            print(f"  Error: {response.status_code}")
    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "=" * 80)
print("Summary")
print("=" * 80)
print("\nDexScreener API:")
print("- Provides basic pair data (price, liquidity, FDV)")
print("- Has 'warnings' field that might indicate issues")
print("- Does not explicitly show liquidity lock status")
print("\nGeckoTerminal API:")
print("- Provides detailed pool and token data")
print("- Does not have explicit liquidity lock fields in standard endpoints")
print("- May need to check security/audit endpoints if available")
print("\nRecommendation:")
print("For liquidity lock info, you may need to:")
print("1. Use specialized services like Token Sniffer, Honeypot.is, or GoPlus Security API")
print("2. Check on-chain data directly for lock contracts")
print("3. Parse warning messages from DexScreener")