#!/usr/bin/env python3
"""Test DexScreener Token Security and GeckoTerminal Security endpoints"""
import requests
import json
import os

# Test tokens
test_tokens = [
    {
        "name": "PEPE", 
        "network": "ethereum",
        "address": "0x6982508145454ce325ddbe47a25d4ec3d2311933",
    },
    {
        "name": "PONKE",
        "network": "solana",
        "address": "5z3EqYQo9HiCEs3R84RCDMu2n7anpDMxRhdK8PSWmrRC"
    },
    {
        "name": "WIF",
        "network": "solana", 
        "address": "EKpQGSJtjMFqKZ9KQanSqYXRcF8fBopzLHYxdM65zcjm"
    }
]

print("=" * 80)
print("Testing DexScreener Token Security Endpoint")
print("=" * 80)

for token in test_tokens:
    print(f"\n{token['name']} ({token['network']})")
    print(f"Contract: {token['address']}")
    
    # DexScreener token endpoint
    token_url = f"https://api.dexscreener.com/latest/dex/tokens/{token['address']}"
    
    try:
        response = requests.get(token_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'pairs' in data and len(data['pairs']) > 0:
                # Get the first/main pair
                pair = data['pairs'][0]
                
                print(f"\nMain Pair Info:")
                print(f"  Pair Address: {pair.get('pairAddress', 'N/A')}")
                print(f"  DEX: {pair.get('dexId', 'N/A')}")
                print(f"  Liquidity: ${pair.get('liquidity', {}).get('usd', 0):,.2f}")
                
                # Check info section for security details
                if 'info' in pair:
                    info = pair['info']
                    print(f"\n  Security/Info Details:")
                    if 'warnings' in info and info['warnings']:
                        print(f"    ⚠️  Warnings: {info['warnings']}")
                    else:
                        print(f"    ✅ No warnings")
                    
                # Check token specific fields
                print(f"\n  Token Details:")
                print(f"    Price: ${pair.get('priceUsd', 'N/A')}")
                print(f"    Market Cap: ${pair.get('marketCap', 0):,.2f}" if pair.get('marketCap') else "    Market Cap: N/A")
                print(f"    FDV: ${pair.get('fdv', 0):,.2f}" if pair.get('fdv') else "    FDV: N/A")
                
                # Check for boosts or badges
                if 'boosts' in pair:
                    print(f"    Boosts: {pair['boosts']}")
                    
        else:
            print(f"  Error: {response.status_code}")
    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "=" * 80)
print("Testing GoPlus Security API (Free Tier)")
print("=" * 80)

# GoPlus Security API - provides detailed security info including liquidity locks
for token in test_tokens:
    print(f"\n{token['name']} ({token['network']})")
    
    # Map network names for GoPlus
    goplus_chain_id = {
        'ethereum': '1',
        'bsc': '56', 
        'polygon': '137',
        'arbitrum': '42161',
        'solana': 'solana'
    }.get(token['network'], token['network'])
    
    # GoPlus token security endpoint
    goplus_url = f"https://api.gopluslabs.io/api/v1/token_security/{goplus_chain_id}"
    params = {'contract_addresses': token['address']}
    
    try:
        response = requests.get(goplus_url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'result' in data and token['address'].lower() in data['result']:
                security = data['result'][token['address'].lower()]
                
                print(f"\n  GoPlus Security Analysis:")
                
                # Liquidity specific checks
                print(f"\n  Liquidity Info:")
                print(f"    Is Open Source: {security.get('is_open_source', 'N/A')}")
                print(f"    Is Proxy: {security.get('is_proxy', 'N/A')}")
                print(f"    Is Mintable: {security.get('is_mintable', 'N/A')}")
                print(f"    Owner Address: {security.get('owner_address', 'N/A')}")
                print(f"    Can Take Back Ownership: {security.get('can_take_back_ownership', 'N/A')}")
                
                # Honeypot related
                print(f"\n  Trading Security:")
                print(f"    Is Honeypot: {security.get('is_honeypot', 'N/A')}")
                print(f"    Buy Tax: {security.get('buy_tax', 'N/A')}")
                print(f"    Sell Tax: {security.get('sell_tax', 'N/A')}")
                print(f"    Cannot Buy: {security.get('cannot_buy', 'N/A')}")
                print(f"    Cannot Sell All: {security.get('cannot_sell_all', 'N/A')}")
                print(f"    Slippage Modifiable: {security.get('slippage_modifiable', 'N/A')}")
                
                # LP related info
                print(f"\n  LP (Liquidity Provider) Info:")
                print(f"    LP Holders: {security.get('lp_holders', 'N/A')}")
                print(f"    LP Total Supply: {security.get('lp_total_supply', 'N/A')}")
                
                # Holder info
                print(f"\n  Holder Info:")
                print(f"    Holder Count: {security.get('holder_count', 'N/A')}")
                print(f"    Total Supply: {security.get('total_supply', 'N/A')}")
                
                # DEX info which might include lock status
                if 'dex' in security:
                    print(f"\n  DEX Info:")
                    for dex in security['dex']:
                        print(f"    {dex.get('name', 'Unknown')}:")
                        print(f"      Liquidity: ${dex.get('liquidity', 0):,.2f}" if dex.get('liquidity') else "      Liquidity: N/A")
                        print(f"      Pair: {dex.get('pair', 'N/A')}")
            else:
                print(f"  No security data found")
        else:
            print(f"  Error: {response.status_code}")
    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "=" * 80)
print("Summary of Findings")
print("=" * 80)
print("\n1. DexScreener API:")
print("   - Provides 'warnings' array that may indicate security issues")
print("   - No direct liquidity lock information")
print("   - Good for basic token metrics and trading data")

print("\n2. GoPlus Security API (Recommended):")
print("   - Free tier available")
print("   - Provides comprehensive security analysis")
print("   - Includes honeypot detection, tax analysis")
print("   - Shows LP holder information")
print("   - Can indicate if contract is renounced/ownership status")

print("\n3. For Liquidity Lock Detection:")
print("   - Check 'owner_address' - if null/0x000, ownership is renounced")
print("   - Check 'lp_holders' - look for known lock contracts")
print("   - Low 'holder_count' + high concentration might indicate unlocked LP")
print("   - 'cannot_sell_all' flag might indicate locked tokens")

print("\nNext Steps:")
print("1. Integrate GoPlus Security API for security checks")
print("2. Add security score fields to database")
print("3. Flag tokens with security warnings in the UI")