#!/usr/bin/env python3
"""
Analyze token launch rates across different networks
"""

import requests
import json
from datetime import datetime, timedelta
from collections import defaultdict

def fetch_new_pools(network, pages=5):
    """Fetch multiple pages of new pools for a network"""
    all_pools = []
    
    for page in range(1, pages + 1):
        url = f"https://api.geckoterminal.com/api/v2/networks/{network}/new_pools?page={page}"
        try:
            response = requests.get(url, headers={'Accept': 'application/json'})
            if response.status_code == 200:
                data = response.json()
                pools = data.get('data', [])
                all_pools.extend(pools)
                print(f"  Page {page}: {len(pools)} pools")
            else:
                print(f"  Error fetching page {page}: {response.status_code}")
                break
        except Exception as e:
            print(f"  Error: {e}")
            break
    
    return all_pools

def analyze_launch_rate(pools):
    """Analyze the launch rate of pools"""
    if not pools:
        return None
    
    # Extract creation times
    timestamps = []
    for pool in pools:
        created_at = pool.get('attributes', {}).get('pool_created_at')
        if created_at:
            # Parse ISO timestamp
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            timestamps.append(dt)
    
    if len(timestamps) < 2:
        return None
    
    # Sort timestamps
    timestamps.sort(reverse=True)
    
    # Calculate time span
    newest = timestamps[0]
    oldest = timestamps[-1]
    time_span = newest - oldest
    
    # Calculate rate
    total_minutes = time_span.total_seconds() / 60
    if total_minutes > 0:
        rate_per_minute = len(timestamps) / total_minutes
    else:
        rate_per_minute = 0
    
    return {
        'total_pools': len(timestamps),
        'newest': newest,
        'oldest': oldest,
        'time_span_minutes': total_minutes,
        'rate_per_minute': rate_per_minute,
        'rate_per_hour': rate_per_minute * 60,
        'rate_per_day': rate_per_minute * 60 * 24
    }

# Networks to analyze
networks = ['solana', 'eth', 'base', 'polygon', 'arbitrum', 'bsc']

print("=" * 60)
print("TOKEN LAUNCH RATE ANALYSIS")
print("=" * 60)
print(f"Current time: {datetime.now().isoformat()}")
print()

total_rate_per_minute = 0
network_stats = {}

for network in networks:
    print(f"\n{network.upper()}")
    print("-" * 40)
    
    # Fetch pools
    print(f"Fetching new pools...")
    pools = fetch_new_pools(network, pages=3)  # Get 3 pages (60 pools)
    
    if pools:
        # Analyze rate
        stats = analyze_launch_rate(pools)
        
        if stats:
            network_stats[network] = stats
            total_rate_per_minute += stats['rate_per_minute']
            
            print(f"\nAnalysis:")
            print(f"  Pools analyzed: {stats['total_pools']}")
            print(f"  Time span: {stats['time_span_minutes']:.1f} minutes")
            print(f"  Newest pool: {stats['newest'].strftime('%H:%M:%S')}")
            print(f"  Oldest pool: {stats['oldest'].strftime('%H:%M:%S')}")
            print(f"  Rate: {stats['rate_per_minute']:.1f} pools/minute")
            print(f"  Rate: {stats['rate_per_hour']:.0f} pools/hour")
            print(f"  Rate: {stats['rate_per_day']:.0f} pools/day")
            
            # Check liquidity distribution
            high_liquidity = 0
            low_liquidity = 0
            
            for pool in pools[:20]:  # Check first 20
                liquidity = float(pool.get('attributes', {}).get('reserve_in_usd', 0))
                if liquidity > 1000:
                    high_liquidity += 1
                elif liquidity > 100:
                    low_liquidity += 1
            
            print(f"  Liquidity distribution (first 20):")
            print(f"    > $1000: {high_liquidity}")
            print(f"    $100-$1000: {low_liquidity}")
            print(f"    < $100: {20 - high_liquidity - low_liquidity}")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

if network_stats:
    print(f"\nTotal networks analyzed: {len(network_stats)}")
    print(f"Combined rate: {total_rate_per_minute:.1f} new pools/minute")
    print(f"Combined rate: {total_rate_per_minute * 60:.0f} new pools/hour")
    print(f"Combined rate: {total_rate_per_minute * 60 * 24:.0f} new pools/day")
    
    print(f"\nBy Network (pools/minute):")
    sorted_networks = sorted(network_stats.items(), key=lambda x: x[1]['rate_per_minute'], reverse=True)
    for network, stats in sorted_networks:
        print(f"  {network:10s}: {stats['rate_per_minute']:6.1f} pools/min ({stats['rate_per_hour']:5.0f}/hour)")
    
    print(f"\nIMPLICATIONS:")
    print(f"- With 10-minute polling interval, you miss ~{int(total_rate_per_minute * 9)} pools")
    print(f"- Current system captures ~{100 / (total_rate_per_minute * 10):.1f}% of all new pools")
    print(f"- To capture 50% of pools, need to poll every {int(20 / total_rate_per_minute)} seconds")
    print(f"- To capture 90% of pools, need to poll every {int(18 / total_rate_per_minute)} seconds")