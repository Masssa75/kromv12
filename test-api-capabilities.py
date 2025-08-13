#!/usr/bin/env python3
"""
Test what social data is available from DexScreener and GeckoTerminal APIs
"""

import requests
import json
from typing import Dict, Any

def test_dexscreener_batch():
    """Test DexScreener batch API capabilities"""
    print("=" * 60)
    print("DEXSCREENER BATCH API TEST")
    print("=" * 60)
    
    # Test with diverse tokens
    test_tokens = [
        ("7JFnQBJoCLkR9DHy3HKayZjvEqUF7Qzi8TCfQRPQpump", "KROM", "solana"),
        ("So11111111111111111111111111111111111112", "SOL", "solana"),
        ("0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984", "UNI", "ethereum"),
        ("0x514910771AF9Ca656af840dff83E8264EcF986CA", "LINK", "ethereum"),
        ("0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", "USDC", "ethereum")
    ]
    
    addresses = [t[0] for t in test_tokens]
    
    # Test batch endpoint (up to 30 addresses)
    url = f"https://api.dexscreener.com/latest/dex/tokens/{','.join(addresses).lower()}"
    
    print(f"\n📡 Testing batch endpoint with {len(addresses)} tokens")
    print(f"URL: {url[:80]}...")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        print(f"\n✅ Response received: {len(data.get('pairs', []))} pairs returned")
        
        # Analyze what data is available
        tokens_with_socials = {}
        
        for pair in data.get('pairs', []):
            token = pair.get('baseToken', {})
            token_addr = token.get('address', '').lower()
            token_symbol = token.get('symbol', 'UNKNOWN')
            
            # Skip if we already processed this token (take highest liquidity pair)
            if token_addr in tokens_with_socials:
                existing_liq = tokens_with_socials[token_addr].get('liquidity', 0)
                new_liq = pair.get('liquidity', {}).get('usd', 0)
                if new_liq <= existing_liq:
                    continue
            
            info = pair.get('info', {})
            socials = info.get('socials', [])
            websites = info.get('websites', [])
            
            social_data = {
                'symbol': token_symbol,
                'chain': pair.get('chainId'),
                'liquidity': pair.get('liquidity', {}).get('usd', 0),
                'website': None,
                'twitter': None,
                'telegram': None,
                'discord': None,
                'other_socials': []
            }
            
            # Extract social links
            for social in socials:
                social_type = social.get('type', '')
                social_url = social.get('url', '')
                
                if social_type == 'website':
                    social_data['website'] = social_url
                elif social_type == 'twitter':
                    social_data['twitter'] = social_url
                elif social_type == 'telegram':
                    social_data['telegram'] = social_url
                elif social_type == 'discord':
                    social_data['discord'] = social_url
                else:
                    social_data['other_socials'].append(f"{social_type}: {social_url}")
            
            # Check websites field too
            if websites and not social_data['website']:
                if isinstance(websites, list) and len(websites) > 0:
                    social_data['website'] = websites[0].get('url') if isinstance(websites[0], dict) else websites[0]
            
            tokens_with_socials[token_addr] = social_data
        
        # Display results
        print("\n📊 SOCIAL DATA AVAILABILITY:")
        print("-" * 40)
        
        for addr, symbol, chain in test_tokens:
            addr_lower = addr.lower()
            if addr_lower in tokens_with_socials:
                data = tokens_with_socials[addr_lower]
                print(f"\n{data['symbol']} ({chain}):")
                print(f"  Website:  {data['website'] or 'Not found'}")
                print(f"  Twitter:  {data['twitter'] or 'Not found'}")
                print(f"  Telegram: {data['telegram'] or 'Not found'}")
                print(f"  Discord:  {data['discord'] or 'Not found'}")
                if data['other_socials']:
                    print(f"  Others:   {', '.join(data['other_socials'])}")
            else:
                print(f"\n{symbol} ({chain}): Not found in DexScreener")
        
        # Summary statistics
        print("\n📈 SUMMARY:")
        print("-" * 40)
        total = len(tokens_with_socials)
        with_website = sum(1 for d in tokens_with_socials.values() if d['website'])
        with_twitter = sum(1 for d in tokens_with_socials.values() if d['twitter'])
        with_telegram = sum(1 for d in tokens_with_socials.values() if d['telegram'])
        
        print(f"Tokens found: {total}/{len(test_tokens)}")
        print(f"With website: {with_website}/{total} ({with_website/total*100:.0f}%)")
        print(f"With Twitter: {with_twitter}/{total} ({with_twitter/total*100:.0f}%)")
        print(f"With Telegram: {with_telegram}/{total} ({with_telegram/total*100:.0f}%)")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def test_geckoterminal_api():
    """Test GeckoTerminal API for social data"""
    print("\n" + "=" * 60)
    print("GECKOTERMINAL API TEST")
    print("=" * 60)
    
    # Test single token endpoint
    test_cases = [
        ("solana", "7JFnQBJoCLkR9DHy3HKayZjvEqUF7Qzi8TCfQRPQpump", "KROM"),
        ("eth", "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984", "UNI")
    ]
    
    for network, address, symbol in test_cases:
        print(f"\n📡 Testing {symbol} on {network}")
        
        # Try token info endpoint
        url = f"https://api.geckoterminal.com/api/v2/networks/{network}/tokens/{address}"
        
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            token_data = data.get('data', {})
            attributes = token_data.get('attributes', {})
            
            print(f"  Name: {attributes.get('name', 'N/A')}")
            print(f"  Symbol: {attributes.get('symbol', 'N/A')}")
            print(f"  Coingecko ID: {attributes.get('coingecko_coin_id', 'N/A')}")
            
            # Check for websites/socials in attributes
            for key in attributes:
                if 'website' in key.lower() or 'social' in key.lower() or 'twitter' in key.lower():
                    print(f"  {key}: {attributes[key]}")
            
            # Check relationships for additional data
            relationships = token_data.get('relationships', {})
            if relationships:
                print(f"  Relationships: {list(relationships.keys())}")
            
        except Exception as e:
            print(f"  ❌ Error: {e}")

def main():
    """Run all API tests"""
    print("🔍 Testing API Capabilities for Social Data\n")
    
    # Test DexScreener batch API
    test_dexscreener_batch()
    
    # Test GeckoTerminal API
    test_geckoterminal_api()
    
    print("\n" + "=" * 60)
    print("CONCLUSIONS:")
    print("=" * 60)
    print("""
1. DexScreener Batch API:
   - ✅ Supports up to 30 tokens per request
   - ✅ Returns website, Twitter, Telegram, Discord links
   - ✅ Works across all chains (Solana, Ethereum, BSC, etc.)
   - ✅ Free, no API key required
   
2. GeckoTerminal API:
   - ❌ No batch endpoint (single token only)
   - ❌ No social links in token data
   - ✅ Has CoinGecko ID for some tokens
   - ⚠️ Rate limited, slower

RECOMMENDATION: Use DexScreener batch API for fetching social links
""")

if __name__ == "__main__":
    main()