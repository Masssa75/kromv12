#!/usr/bin/env python3
"""Batch process tokens for security analysis using GoPlus API"""
import requests
import time
import json
from datetime import datetime
# Import the functions directly
import requests as req

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
        response = req.get(url, params=params, timeout=10)
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

def process_batch(limit=10):
    """Process a batch of tokens for security analysis"""
    
    # Get tokens that haven't been checked yet, prioritizing high-score tokens
    query = f"""
    SELECT id, ticker, contract_address, network, analysis_score, x_analysis_score
    FROM crypto_calls
    WHERE security_checked_at IS NULL
    AND contract_address IS NOT NULL
    AND network IN ('ethereum', 'eth', 'bsc', 'polygon', 'arbitrum', 'base', 'avalanche')
    ORDER BY 
        CASE WHEN analysis_score >= 7 OR x_analysis_score >= 7 THEN 1 ELSE 0 END DESC,
        created_at DESC
    LIMIT {limit}
    """
    
    tokens = run_query(query)
    
    if not tokens:
        print("No tokens to process")
        return 0
    
    print(f"Processing {len(tokens)} tokens...")
    processed = 0
    
    for token in tokens:
        print(f"\nAnalyzing {token['ticker']} on {token['network']}...")
        
        try:
            # Fetch security data
            security_data = fetch_goplus_security(token['contract_address'], token['network'])
            
            # Analyze
            analysis = analyze_liquidity_lock(security_data)
            
            # Update database with both analyzed data and raw data
            raw_data_json = json.dumps(security_data).replace("'", "''") if security_data else 'null'
            
            update_query = f"""
            UPDATE crypto_calls SET
                liquidity_locked = {analysis['is_locked']},
                liquidity_lock_percent = {analysis['lock_percent']},
                ownership_renounced = {analysis['ownership_renounced']},
                security_score = {analysis['security_score']},
                security_warnings = '{json.dumps(analysis['warnings']).replace("'", "''")}',
                security_raw_data = '{raw_data_json}'::jsonb,
                security_checked_at = NOW()
            WHERE id = '{token['id']}'
            """
            
            result = run_query(update_query)
            
            print(f"  Security Score: {analysis['security_score']}/100")
            print(f"  Liquidity Locked: {'Yes' if analysis['is_locked'] else 'No'} ({analysis['lock_percent']:.2f}%)")
            print(f"  Ownership Renounced: {'Yes' if analysis['ownership_renounced'] else 'No'}")
            if analysis['warnings']:
                print(f"  Warnings: {', '.join(analysis['warnings'])}")
            
            processed += 1
            
            # Respect API rate limits (free tier)
            time.sleep(1)
            
        except Exception as e:
            print(f"  Error processing {token['ticker']}: {e}")
            # Mark as checked even on error to avoid retrying bad tokens
            error_query = f"""
            UPDATE crypto_calls SET
                security_checked_at = NOW(),
                security_warnings = '["Error during security check"]'
            WHERE id = '{token['id']}'
            """
            run_query(error_query)
    
    return processed

def get_stats():
    """Get security analysis statistics"""
    stats_query = """
    SELECT 
        COUNT(*) as total_tokens,
        COUNT(security_checked_at) as checked_tokens,
        COUNT(CASE WHEN liquidity_locked = true THEN 1 END) as locked_tokens,
        COUNT(CASE WHEN ownership_renounced = true THEN 1 END) as renounced_tokens,
        COUNT(CASE WHEN security_score >= 80 THEN 1 END) as high_security_tokens,
        COUNT(CASE WHEN security_score < 50 THEN 1 END) as low_security_tokens,
        AVG(security_score) as avg_security_score
    FROM crypto_calls
    WHERE contract_address IS NOT NULL
    AND network IN ('ethereum', 'eth', 'bsc', 'polygon', 'arbitrum', 'base', 'avalanche')
    """
    
    stats = run_query(stats_query)
    if stats:
        return stats[0]
    return None

if __name__ == "__main__":
    print("=" * 60)
    print("Batch Security Analysis for Crypto Tokens")
    print("=" * 60)
    
    # Get initial stats
    stats = get_stats()
    if stats:
        print(f"\nCurrent Status:")
        print(f"  Total eligible tokens: {stats['total_tokens']}")
        print(f"  Already checked: {stats['checked_tokens']}")
        print(f"  Remaining: {stats['total_tokens'] - stats['checked_tokens']}")
        
        if stats['checked_tokens'] > 0:
            print(f"\nSecurity Stats:")
            print(f"  Tokens with locked liquidity: {stats['locked_tokens']}")
            print(f"  Tokens with renounced ownership: {stats['renounced_tokens']}")
            print(f"  High security (80+): {stats['high_security_tokens']}")
            print(f"  Low security (<50): {stats['low_security_tokens']}")
            if stats['avg_security_score'] is not None:
                print(f"  Average security score: {float(stats['avg_security_score']):.1f}")
            else:
                print(f"  Average security score: N/A")
    
    print("\n" + "-" * 60)
    
    # Process batch - 50 latest tokens as requested
    processed = process_batch(limit=50)
    
    print("\n" + "-" * 60)
    print(f"Processed {processed} tokens")
    
    # Get updated stats
    stats = get_stats()
    if stats:
        print(f"\nUpdated Status:")
        print(f"  Total checked: {stats['checked_tokens']} / {stats['total_tokens']}")
        print(f"  Progress: {(stats['checked_tokens'] / stats['total_tokens'] * 100):.1f}%")