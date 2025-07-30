#!/usr/bin/env python3
"""Fetch token security data including liquidity lock status using GoPlus API"""
import requests
import time
from datetime import datetime

# Configuration
MANAGEMENT_TOKEN = "sbp_97ca99b1a82b9ed514d259a119ea3c19a2e42cd7"
PROJECT_REF = "eucfoommxxvqmmwdbkdv"

def run_query(query):
    """Execute Supabase query"""
    try:
        response = requests.post(
            f"https://api.supabase.com/v1/projects/{PROJECT_REF}/database/query",
            headers={"Authorization": f"Bearer {MANAGEMENT_TOKEN}", "Content-Type": "application/json"},
            json={"query": query},
            timeout=10
        )
        return response.json()
    except Exception as e:
        print(f"Query error: {e}")
        return []

def fetch_goplus_security(contract_address, network):
    """Fetch security data from GoPlus API"""
    # Map network names to chain IDs
    chain_map = {
        'ethereum': '1',
        'eth': '1',
        'bsc': '56',
        'polygon': '137',
        'arbitrum': '42161',
        'solana': 'solana',
        'base': '8453',
        'avalanche': '43114'
    }
    
    chain_id = chain_map.get(network.lower(), network)
    
    # Skip unsupported networks
    if chain_id not in ['1', '56', '137', '42161', 'solana', '8453', '43114']:
        return None
    
    url = f"https://api.gopluslabs.io/api/v1/token_security/{chain_id}"
    params = {'contract_addresses': contract_address.lower()}
    
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'result' in data and contract_address.lower() in data['result']:
                return data['result'][contract_address.lower()]
    except Exception as e:
        print(f"GoPlus API error for {contract_address}: {e}")
    
    return None

def analyze_liquidity_lock(security_data):
    """Analyze security data to determine liquidity lock status"""
    if not security_data:
        return {
            'is_locked': None,
            'lock_percent': 0,
            'ownership_renounced': None,
            'security_score': 0,
            'warnings': ['No security data available']
        }
    
    result = {
        'is_locked': False,
        'lock_percent': 0,
        'ownership_renounced': False,
        'security_score': 100,  # Start with 100, deduct for issues
        'warnings': []
    }
    
    # Check ownership
    owner = security_data.get('owner_address', '')
    if owner == '0x0000000000000000000000000000000000000000' or owner == '':
        result['ownership_renounced'] = True
        result['security_score'] += 10  # Bonus for renounced ownership
    
    # Check LP holders for locks
    lp_holders = security_data.get('lp_holders', [])
    total_locked_percent = 0
    
    for holder in lp_holders:
        if holder.get('is_locked') == 1:
            percent = float(holder.get('percent', 0))
            total_locked_percent += percent
            
            # Known lock/burn addresses
            if holder['address'].lower() in [
                '0x000000000000000000000000000000000000dead',
                '0x0000000000000000000000000000000000000001',
                '0x0000000000000000000000000000000000000000'
            ]:
                result['is_locked'] = True
    
    result['lock_percent'] = total_locked_percent * 100
    
    # Check for red flags
    if security_data.get('is_honeypot') == '1':
        result['warnings'].append('Honeypot detected')
        result['security_score'] -= 50
        
    if security_data.get('is_mintable') == '1':
        result['warnings'].append('Token is mintable')
        result['security_score'] -= 20
        
    buy_tax = float(security_data.get('buy_tax', 0))
    sell_tax = float(security_data.get('sell_tax', 0))
    
    if buy_tax > 10:
        result['warnings'].append(f'High buy tax: {buy_tax}%')
        result['security_score'] -= 15
        
    if sell_tax > 10:
        result['warnings'].append(f'High sell tax: {sell_tax}%')
        result['security_score'] -= 15
        
    if security_data.get('cannot_sell_all') == '1':
        result['warnings'].append('Cannot sell all tokens')
        result['security_score'] -= 25
        
    if security_data.get('can_take_back_ownership') == '1':
        result['warnings'].append('Ownership can be taken back')
        result['security_score'] -= 20
    
    # Bonus for locked liquidity
    if result['lock_percent'] > 50:
        result['security_score'] += 15
    elif result['lock_percent'] > 20:
        result['security_score'] += 10
    
    # Cap score between 0-100
    result['security_score'] = max(0, min(100, result['security_score']))
    
    return result

# Example usage
if __name__ == "__main__":
    print("Testing token security analysis...")
    
    # Test tokens
    test_tokens = [
        {"ticker": "PEPE", "address": "0x6982508145454ce325ddbe47a25d4ec3d2311933", "network": "ethereum"},
        {"ticker": "SHIB", "address": "0x95ad61b0a150d79219dcf64e1e6cc01f0b64c4ce", "network": "ethereum"},
        {"ticker": "PONKE", "address": "5z3EqYQo9HiCEs3R84RCDMu2n7anpDMxRhdK8PSWmrRC", "network": "solana"}
    ]
    
    for token in test_tokens:
        print(f"\n{'='*60}")
        print(f"Analyzing {token['ticker']} on {token['network']}")
        print(f"Contract: {token['address']}")
        
        # Fetch security data
        security_data = fetch_goplus_security(token['address'], token['network'])
        
        # Analyze
        analysis = analyze_liquidity_lock(security_data)
        
        print(f"\nSecurity Analysis:")
        print(f"  Liquidity Locked: {'Yes' if analysis['is_locked'] else 'No'}")
        print(f"  Lock Percentage: {analysis['lock_percent']:.2f}%")
        print(f"  Ownership Renounced: {'Yes' if analysis['ownership_renounced'] else 'No'}")
        print(f"  Security Score: {analysis['security_score']}/100")
        
        if analysis['warnings']:
            print(f"  Warnings:")
            for warning in analysis['warnings']:
                print(f"    - {warning}")
        
        # Add 1 second delay to respect API rate limits
        time.sleep(1)
    
    print(f"\n{'='*60}")
    print("\nTo integrate this into the database:")
    print("1. Add columns: liquidity_locked, lock_percent, ownership_renounced, security_score, security_warnings")
    print("2. Run this analysis for all tokens periodically")
    print("3. Display security info in the UI with appropriate warnings")