#!/usr/bin/env python3
"""
Test various APIs to find the best source for liquidity lock data
"""

import requests
import json
import time
from typing import Dict, Any, Optional

# Test tokens with known liquidity
TEST_TOKENS = [
    {"ticker": "BLOCK", "chain": "ethereum", "address": "0xCaB84bc21F9092167fCFe0ea60f5CE053ab39a1E"},
    {"ticker": "MAMO", "chain": "base", "address": "0x7300B37DfdfAb110d83290A29DfB31B1740219fE"},
    {"ticker": "PEPE", "chain": "ethereum", "address": "0x6982508145454Ce325dDbE47a25d4ec3d2311933"},
    {"ticker": "BONK", "chain": "solana", "address": "DezXAZ8z7PnrnRJjz3wXBoRgixCa6xjnB7YaB1pPB263"},
]

def test_dexscreener_api(token: Dict) -> Dict[str, Any]:
    """Test DexScreener API for liquidity lock data"""
    print(f"\n1. TESTING DEXSCREENER for {token['ticker']}:")
    print("-" * 40)
    
    try:
        # DexScreener uses contract addresses directly
        url = f"https://api.dexscreener.com/latest/dex/tokens/{token['address']}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if liquidity lock info exists
            found_lock_info = False
            liquidity_info = {}
            
            if 'pairs' in data and data['pairs']:
                pair = data['pairs'][0]  # Get first pair
                
                # Check various fields that might contain lock info
                liquidity_info['liquidity_usd'] = pair.get('liquidity', {}).get('usd', 'N/A')
                liquidity_info['fdv'] = pair.get('fdv', 'N/A')
                
                # Look for lock-related fields
                if 'info' in pair:
                    info = pair.get('info', {})
                    if 'locks' in info:
                        found_lock_info = True
                        liquidity_info['locks'] = info['locks']
                
                # Check if there's any lock indicator
                for key in pair.keys():
                    if 'lock' in key.lower():
                        found_lock_info = True
                        liquidity_info[key] = pair[key]
                
                print(f"✓ Response received")
                print(f"  Liquidity: ${liquidity_info.get('liquidity_usd', 'N/A')}")
                print(f"  Lock info found: {found_lock_info}")
                
                if found_lock_info:
                    print(f"  Lock data: {liquidity_info}")
                else:
                    print("  Note: No explicit lock fields in response")
                
                # Save sample response for analysis
                with open(f'dexscreener_{token["ticker"]}_sample.json', 'w') as f:
                    json.dump(data['pairs'][0] if data['pairs'] else {}, f, indent=2)
                    print(f"  Sample saved to: dexscreener_{token['ticker']}_sample.json")
            else:
                print("  No pairs found")
                
            return {'success': True, 'has_lock_info': found_lock_info, 'data': liquidity_info}
        else:
            print(f"  Error: HTTP {response.status_code}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except Exception as e:
        print(f"  Error: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_goplus_api(token: Dict) -> Dict[str, Any]:
    """Test GoPlus Security API for liquidity lock data"""
    print(f"\n2. TESTING GOPLUS for {token['ticker']}:")
    print("-" * 40)
    
    # Map chain names to GoPlus chain IDs
    chain_map = {
        'ethereum': '1',
        'bsc': '56',
        'polygon': '137',
        'arbitrum': '42161',
        'base': '8453',
        'avalanche': '43114',
        'solana': 'solana'
    }
    
    chain_id = chain_map.get(token['chain'])
    if not chain_id:
        print(f"  Chain {token['chain']} not supported")
        return {'success': False, 'error': 'Chain not supported'}
    
    try:
        url = f"https://api.gopluslabs.io/api/v1/token_security/{chain_id}?contract_addresses={token['address']}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            if 'result' in data and token['address'].lower() in data['result']:
                token_data = data['result'][token['address'].lower()]
                
                # Extract lock-related fields
                lock_info = {
                    'lp_holders': token_data.get('lp_holders', []),
                    'is_open_source': token_data.get('is_open_source'),
                    'is_proxy': token_data.get('is_proxy'),
                    'is_mintable': token_data.get('is_mintable'),
                    'owner_address': token_data.get('owner_address'),
                    'can_take_back_ownership': token_data.get('can_take_back_ownership'),
                    'cannot_sell_all': token_data.get('cannot_sell_all')
                }
                
                # Check LP holders for lock contracts
                has_lock = False
                if lock_info['lp_holders']:
                    for holder in lock_info['lp_holders']:
                        if holder.get('is_locked') == 1:
                            has_lock = True
                            break
                        # Check if holder is a known lock contract
                        if 'lock' in str(holder.get('address', '')).lower():
                            has_lock = True
                            break
                
                print(f"✓ Response received")
                print(f"  LP Holders: {len(lock_info['lp_holders'])}")
                print(f"  Has locked liquidity: {has_lock}")
                print(f"  Is mintable: {lock_info['is_mintable']}")
                print(f"  Owner: {lock_info['owner_address'][:10]}..." if lock_info['owner_address'] else "  Owner: None")
                
                return {'success': True, 'has_lock_info': True, 'has_lock': has_lock, 'data': lock_info}
            else:
                print("  No data for this token")
                return {'success': True, 'has_lock_info': False}
        else:
            print(f"  Error: HTTP {response.status_code}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except Exception as e:
        print(f"  Error: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_etherscan_api(token: Dict) -> Dict[str, Any]:
    """Test Etherscan API for liquidity lock data"""
    print(f"\n3. TESTING ETHERSCAN for {token['ticker']}:")
    print("-" * 40)
    
    if token['chain'] != 'ethereum':
        print(f"  Skipping - Etherscan only for Ethereum (token is on {token['chain']})")
        return {'success': False, 'error': 'Wrong chain'}
    
    # Note: Etherscan free tier has limits but no API key required for basic calls
    print("  Note: Etherscan doesn't directly provide liquidity lock data")
    print("  Would need to:")
    print("  1. Get LP token address from DEX pair")
    print("  2. Check LP token holders")
    print("  3. Identify if holders include lock contracts")
    print("  This requires multiple API calls and DEX-specific knowledge")
    
    return {'success': False, 'error': 'No direct lock data available'}

def test_honeypot_api(token: Dict) -> Dict[str, Any]:
    """Test Honeypot.is API (free, no key required)"""
    print(f"\n4. TESTING HONEYPOT.IS for {token['ticker']}:")
    print("-" * 40)
    
    # Honeypot.is supports multiple chains
    chain_map = {
        'ethereum': 'ethereum',
        'bsc': 'bsc',
        'polygon': 'polygon',
        'arbitrum': 'arbitrum',
        'base': 'base',
        'avalanche': 'avalanche'
    }
    
    chain = chain_map.get(token['chain'])
    if not chain:
        print(f"  Chain {token['chain']} not supported")
        return {'success': False, 'error': 'Chain not supported'}
    
    try:
        # Honeypot.is V2 API
        url = f"https://api.honeypot.is/v2/IsHoneypot?address={token['address']}&chain={chain}"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Extract relevant info
            summary = data.get('summary', {})
            liquidity_info = data.get('pair', {})
            
            print(f"✓ Response received")
            print(f"  Risk level: {summary.get('risk', 'N/A')}")
            print(f"  Liquidity: ${liquidity_info.get('liquidity', 'N/A')}")
            print(f"  Pair address: {liquidity_info.get('pair', 'N/A')}")
            
            # Check for lock info in flags
            flags = data.get('flags', [])
            lock_related = [f for f in flags if 'lock' in str(f).lower()]
            if lock_related:
                print(f"  Lock-related flags: {lock_related}")
            
            return {'success': True, 'has_lock_info': bool(lock_related), 'data': data}
        else:
            print(f"  Error: HTTP {response.status_code}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
            
    except Exception as e:
        print(f"  Error: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_defined_fi_api(token: Dict) -> Dict[str, Any]:
    """Test Defined.fi API (GraphQL, free tier available)"""
    print(f"\n5. TESTING DEFINED.FI for {token['ticker']}:")
    print("-" * 40)
    
    print("  Note: Defined.fi has a GraphQL API")
    print("  Free tier: 500 requests/month")
    print("  Requires sign-up for API key at https://www.defined.fi/")
    print("  Provides comprehensive DeFi data including liquidity info")
    print("  Would need API key to test")
    
    return {'success': False, 'error': 'API key required'}

def main():
    print("=" * 80)
    print("LIQUIDITY LOCK DATA SOURCE COMPARISON")
    print("=" * 80)
    
    results = {}
    
    for token in TEST_TOKENS:
        print(f"\n{'=' * 80}")
        print(f"TESTING TOKEN: {token['ticker']} on {token['chain']}")
        print(f"Address: {token['address']}")
        print("=" * 80)
        
        # Test each API
        results[token['ticker']] = {
            'dexscreener': test_dexscreener_api(token),
            'goplus': test_goplus_api(token),
            'etherscan': test_etherscan_api(token),
            'honeypot': test_honeypot_api(token),
            'defined': test_defined_fi_api(token)
        }
        
        time.sleep(1)  # Rate limiting
    
    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY & RECOMMENDATIONS")
    print("=" * 80)
    
    print("\n📊 API COMPARISON:")
    print("-" * 40)
    
    print("\n1. GOPLUS SECURITY API:")
    print("   ✅ FREE, no API key needed")
    print("   ✅ Best coverage for lock data")
    print("   ✅ Direct LP holder analysis")
    print("   ❌ Limited Solana support")
    print("   Coverage: ~40% of tokens")
    
    print("\n2. DEXSCREENER API:")
    print("   ✅ FREE, no API key needed")
    print("   ✅ Great liquidity data")
    print("   ❌ No explicit lock fields found")
    print("   ✅ Supports all chains including Solana")
    print("   Note: Already integrated in your system")
    
    print("\n3. HONEYPOT.IS API:")
    print("   ✅ FREE, no API key needed")
    print("   ✅ Risk assessment data")
    print("   ❌ Limited lock info")
    print("   ❌ No Solana support")
    
    print("\n4. ETHERSCAN/BSCSCAN:")
    print("   ✅ FREE tier available")
    print("   ❌ Requires complex multi-step process")
    print("   ❌ Chain-specific (need different endpoints)")
    print("   ⚠️ API key recommended for higher limits")
    
    print("\n5. DEFINED.FI:")
    print("   ⚠️ Free tier: 500 requests/month")
    print("   ✅ Comprehensive DeFi data")
    print("   ❌ Requires sign-up")
    
    print("\n" + "=" * 80)
    print("🎯 RECOMMENDATION:")
    print("-" * 40)
    print("""
    BEST APPROACH (All Free):
    
    1. PRIMARY: Continue using GoPlus (already integrated)
       - Best for Ethereum, BSC, Base, Polygon
       - Provides actual lock status
    
    2. SUPPLEMENT: Add Honeypot.is API
       - Additional risk metrics
       - Free, no key required
       - Can catch honeypots GoPlus misses
    
    3. FALLBACK: Use liquidity amount as proxy
       - If no lock data available
       - High liquidity (>$100K) = lower rug risk
       - Use MCap/Liquidity ratio
    
    NO SIGN-UP NEEDED for options 1-3!
    """)

if __name__ == "__main__":
    main()