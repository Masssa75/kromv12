#!/usr/bin/env python3
"""
Check token discovery coverage by comparing GeckoTerminal new pools with our database
"""
import requests
import json
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

def get_gecko_pools(network, hours_back=2):
    """Fetch recent pools from GeckoTerminal"""
    pools = []
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    
    # Fetch up to 5 pages to get enough historical data
    for page in range(1, 6):
        try:
            response = requests.get(
                f'https://api.geckoterminal.com/api/v2/networks/{network}/new_pools?page={page}',
                headers={'Accept': 'application/json'}
            )
            
            if response.status_code != 200:
                break
                
            data = response.json()
            page_pools = data.get('data', [])
            
            for pool in page_pools:
                created_at_str = pool['attributes'].get('pool_created_at')
                if created_at_str:
                    created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
                    if created_at < cutoff_time:
                        # Stop when we reach pools older than our cutoff
                        return pools
                
                # Extract token address
                base_token = pool.get('relationships', {}).get('base_token', {}).get('data', {})
                token_id = base_token.get('id', '')
                token_address = token_id.split('_')[-1] if token_id else None
                
                if token_address:
                    pools.append({
                        'address': token_address,
                        'symbol': pool['attributes'].get('name', '').split(' / ')[0],
                        'created_at': created_at_str,
                        'liquidity': pool['attributes'].get('reserve_in_usd', 0)
                    })
                    
        except Exception as e:
            print(f"Error fetching page {page}: {e}")
            break
            
    return pools

def check_token_in_db(token_address):
    """Check if a token exists in our database"""
    headers = {
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Content-Type': 'application/json'
    }
    
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/token_discovery?contract_address=eq.{token_address}&select=id",
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        return len(data) > 0
    return False

def analyze_coverage():
    """Analyze discovery coverage for each network"""
    networks = {
        'eth': 'Ethereum',
        'base': 'Base'
    }
    
    print("=" * 80)
    print("TOKEN DISCOVERY COVERAGE ANALYSIS")
    print(f"Checking pools from last 1 hour as of {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("=" * 80)
    
    total_found = 0
    total_missed = 0
    
    for network_key, network_name in networks.items():
        print(f"\n{network_name}:")
        print("-" * 40)
        
        gecko_pools = get_gecko_pools(network_key, hours_back=1)
        
        # Filter pools with >$100 liquidity (our threshold)
        significant_pools = [p for p in gecko_pools if float(p.get('liquidity', 0)) > 100]
        
        found = 0
        missed = []
        
        for pool in significant_pools:
            if check_token_in_db(pool['address']):
                found += 1
            else:
                missed.append(pool)
        
        coverage = (found / len(significant_pools) * 100) if significant_pools else 0
        
        print(f"Total pools with >$100 liquidity: {len(significant_pools)}")
        print(f"Found in DB: {found}")
        print(f"Missed: {len(missed)}")
        print(f"Coverage: {coverage:.1f}%")
        
        if missed and len(missed) <= 5:
            print("\nMissed tokens:")
            for m in missed[:5]:
                liquidity = float(m.get('liquidity', 0))
                print(f"  - {m['symbol']}: ${liquidity:,.0f} liquidity, created {m['created_at']}")
                print(f"    Address: {m['address']}")
        elif len(missed) > 5:
            print(f"\nShowing first 5 of {len(missed)} missed tokens:")
            for m in missed[:5]:
                liquidity = float(m.get('liquidity', 0))
                print(f"  - {m['symbol']}: ${liquidity:,.0f} liquidity")
        
        total_found += found
        total_missed += len(missed)
    
    print("\n" + "=" * 80)
    print("OVERALL SUMMARY")
    print("=" * 80)
    overall_coverage = (total_found / (total_found + total_missed) * 100) if (total_found + total_missed) > 0 else 0
    print(f"Total tokens found: {total_found}")
    print(f"Total tokens missed: {total_missed}")
    print(f"Overall coverage: {overall_coverage:.1f}%")
    
    if overall_coverage < 90:
        print("\n⚠️  Coverage is below 90% - consider increasing pages fetched")
    else:
        print("\n✅ Good coverage! Discovery system is catching most new tokens")

if __name__ == "__main__":
    analyze_coverage()