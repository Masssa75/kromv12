#!/usr/bin/env python3
"""
DexScreener Signal Finder - Identifies tokens worth X/Twitter research
"""
import requests
import json
from datetime import datetime, timedelta
import time

def get_token_pairs(token_address, chain_id=None):
    """Get all trading pairs for a token"""
    url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json().get('pairs', [])
    except:
        pass
    return []

def analyze_signals():
    """Find tokens with interesting signals that deserve X research"""
    
    print("🚀 DexScreener Signal Analysis")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    signals = {
        'new_launches': [],
        'volume_spikes': [],
        'high_activity': [],
        'boosted_new': []
    }
    
    # 1. Check boosted tokens (often new projects with marketing budget)
    print("\n📢 CHECKING BOOSTED TOKENS...")
    try:
        response = requests.get("https://api.dexscreener.com/token-boosts/latest/v1")
        if response.status_code == 200:
            boosts = response.json()[:20]  # Check top 20
            
            for boost in boosts:
                token_address = boost.get('tokenAddress')
                if token_address:
                    pairs = get_token_pairs(token_address)
                    if pairs:
                        main_pair = pairs[0]  # Most liquid pair
                        
                        # Check if it's a new token (less than 7 days old)
                        created_at = main_pair.get('pairCreatedAt')
                        if created_at:
                            age_hours = (time.time() * 1000 - created_at) / (1000 * 3600)
                            
                            if age_hours < 168:  # Less than 7 days
                                liquidity_usd = main_pair.get('liquidity', {}).get('usd', 0)
                                volume_24h = main_pair.get('volume', {}).get('h24', 0)
                                
                                if liquidity_usd > 50000:  # At least $50k liquidity
                                    signals['boosted_new'].append({
                                        'symbol': main_pair.get('baseToken', {}).get('symbol', 'N/A'),
                                        'chain': main_pair.get('chainId', 'N/A'),
                                        'address': token_address,
                                        'age_hours': age_hours,
                                        'liquidity_usd': liquidity_usd,
                                        'volume_24h': volume_24h,
                                        'boost_amount': boost.get('totalAmount', 0),
                                        'url': main_pair.get('url', '')
                                    })
    except Exception as e:
        print(f"Error checking boosts: {e}")
    
    # 2. Search for high-activity new tokens
    print("\n🔥 SEARCHING FOR HIGH-ACTIVITY TOKENS...")
    chains = ['ethereum', 'bsc', 'polygon', 'arbitrum', 'base', 'solana']
    
    for chain in chains:
        try:
            # Search for USDT/USDC pairs on each chain
            response = requests.get(f"https://api.dexscreener.com/latest/dex/search?q=USDT")
            if response.status_code == 200:
                pairs = response.json().get('pairs', [])
                
                # Filter for specific chain and recent pairs
                chain_pairs = [p for p in pairs if p.get('chainId') == chain]
                
                for pair in chain_pairs[:10]:  # Check top 10 per chain
                    created_at = pair.get('pairCreatedAt')
                    if created_at:
                        age_hours = (time.time() * 1000 - created_at) / (1000 * 3600)
                        
                        # New tokens (less than 48 hours)
                        if age_hours < 48:
                            liquidity_usd = pair.get('liquidity', {}).get('usd', 0)
                            volume_24h = pair.get('volume', {}).get('h24', 0)
                            txns_24h = pair.get('txns', {}).get('h24', {})
                            total_txns = txns_24h.get('buys', 0) + txns_24h.get('sells', 0)
                            
                            # High activity threshold
                            if liquidity_usd > 100000 and total_txns > 500:
                                signals['new_launches'].append({
                                    'symbol': pair.get('baseToken', {}).get('symbol', 'N/A'),
                                    'chain': chain,
                                    'address': pair.get('baseToken', {}).get('address', ''),
                                    'age_hours': age_hours,
                                    'liquidity_usd': liquidity_usd,
                                    'volume_24h': volume_24h,
                                    'total_txns_24h': total_txns,
                                    'price_change_24h': pair.get('priceChange', {}).get('h24', 0),
                                    'url': pair.get('url', '')
                                })
                        
                        # Volume spike detection (any age)
                        volume_h24 = pair.get('volume', {}).get('h24', 0)
                        volume_h6 = pair.get('volume', {}).get('h6', 0)
                        
                        if volume_h6 > 0:
                            volume_spike_6h = (volume_h6 * 4) / volume_h24 if volume_h24 > 0 else 0
                            
                            # If 6h volume projects to >2x the 24h volume
                            if volume_spike_6h > 2 and volume_h6 > 50000:
                                signals['volume_spikes'].append({
                                    'symbol': pair.get('baseToken', {}).get('symbol', 'N/A'),
                                    'chain': chain,
                                    'address': pair.get('baseToken', {}).get('address', ''),
                                    'volume_spike_ratio': volume_spike_6h,
                                    'volume_6h': volume_h6,
                                    'volume_24h': volume_h24,
                                    'liquidity_usd': pair.get('liquidity', {}).get('usd', 0),
                                    'price_change_6h': pair.get('priceChange', {}).get('h6', 0),
                                    'url': pair.get('url', '')
                                })
            
            time.sleep(0.5)  # Rate limiting
            
        except Exception as e:
            print(f"Error searching {chain}: {e}")
    
    # Display results
    print("\n" + "=" * 80)
    print("📊 SIGNALS FOUND - TOKENS WORTH X/TWITTER RESEARCH:")
    print("=" * 80)
    
    print(f"\n🆕 NEW HIGH-ACTIVITY LAUNCHES ({len(signals['new_launches'])} found):")
    for token in sorted(signals['new_launches'], key=lambda x: x['volume_24h'], reverse=True)[:5]:
        print(f"\n  ${token['symbol']} on {token['chain']}")
        print(f"  - Age: {token['age_hours']:.1f} hours old")
        print(f"  - Liquidity: ${token['liquidity_usd']:,.0f}")
        print(f"  - 24h Volume: ${token['volume_24h']:,.0f}")
        print(f"  - 24h Transactions: {token['total_txns_24h']:,}")
        print(f"  - 24h Price Change: {token['price_change_24h']:.1f}%")
        print(f"  - Contract: {token['address'][:10]}...")
        print(f"  - URL: {token['url']}")
    
    print(f"\n📈 VOLUME SPIKES ({len(signals['volume_spikes'])} found):")
    for token in sorted(signals['volume_spikes'], key=lambda x: x['volume_spike_ratio'], reverse=True)[:5]:
        print(f"\n  ${token['symbol']} on {token['chain']}")
        print(f"  - Volume Spike: {token['volume_spike_ratio']:.1f}x projected")
        print(f"  - 6h Volume: ${token['volume_6h']:,.0f}")
        print(f"  - 6h Price Change: {token['price_change_6h']:.1f}%")
        print(f"  - Liquidity: ${token['liquidity_usd']:,.0f}")
        print(f"  - Contract: {token['address'][:10]}...")
    
    print(f"\n💎 BOOSTED NEW TOKENS ({len(signals['boosted_new'])} found):")
    for token in sorted(signals['boosted_new'], key=lambda x: x['boost_amount'], reverse=True)[:5]:
        print(f"\n  ${token['symbol']} on {token['chain']}")
        print(f"  - Age: {token['age_hours']:.1f} hours old")
        print(f"  - Boost Amount: {token['boost_amount']}")
        print(f"  - Liquidity: ${token['liquidity_usd']:,.0f}")
        print(f"  - 24h Volume: ${token['volume_24h']:,.0f}")
        print(f"  - Contract: {token['address'][:10]}...")
    
    # Save signals to JSON
    with open('dexscreener-signals.json', 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'signals': signals
        }, f, indent=2)
    
    print(f"\n\n💾 Full signal data saved to: dexscreener-signals.json")
    
    # Recommendations
    print("\n" + "=" * 80)
    print("🎯 RECOMMENDED X/TWITTER RESEARCH PRIORITIES:")
    print("=" * 80)
    print("\n1. NEW LAUNCHES (<48h) with high activity - likely to have fresh social buzz")
    print("2. VOLUME SPIKES - something is happening, check for news/announcements")
    print("3. BOOSTED TOKENS - teams spending money on marketing, check their Twitter")
    
    return signals

if __name__ == "__main__":
    analyze_signals()