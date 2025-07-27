#!/usr/bin/env python3
"""
Fix for DexScreener API - use search endpoint which we know works
"""
import requests
import time
from datetime import datetime

def get_dexscreener_signals_fixed():
    """Fixed version using search endpoint"""
    
    signals = {
        'new_launches': [],
        'volume_spikes': [],
        'boosted_tokens': []
    }
    
    # We know boosted tokens work, so keep that as is
    
    # For new launches and volume spikes, use search endpoint
    print("Testing new approach with search endpoint...")
    
    # Search for popular pairs on each chain
    search_queries = [
        'SOL',      # Solana pairs
        'ETH',      # Ethereum pairs
        'WETH',     # Wrapped ETH pairs
        'BNB',      # BSC pairs
        'USDC',     # Stablecoin pairs
        'USDT'      # Tether pairs
    ]
    
    all_pairs = []
    seen_addresses = set()
    
    for query in search_queries:
        try:
            print(f"\nSearching for {query} pairs...")
            response = requests.get(f"https://api.dexscreener.com/latest/dex/search?q={query}")
            
            if response.status_code == 200:
                data = response.json()
                pairs = data.get('pairs', [])
                print(f"  Found {len(pairs)} pairs")
                
                # Add unique pairs
                for pair in pairs:
                    address = pair.get('baseToken', {}).get('address', '')
                    if address and address not in seen_addresses:
                        seen_addresses.add(address)
                        all_pairs.append(pair)
                
            time.sleep(0.3)  # Rate limiting
            
        except Exception as e:
            print(f"  Error: {e}")
    
    print(f"\nTotal unique pairs collected: {len(all_pairs)}")
    
    # Now analyze for signals
    new_count = 0
    spike_count = 0
    
    for pair in all_pairs:
        try:
            created_at = pair.get('pairCreatedAt')
            if created_at:
                age_hours = (time.time() * 1000 - created_at) / (1000 * 3600)
                
                # New launches (very relaxed criteria)
                if age_hours < 168:  # Less than 7 days
                    liquidity_usd = pair.get('liquidity', {}).get('usd', 0)
                    
                    if liquidity_usd > 5000:  # Just $5k liquidity
                        new_count += 1
                        if len(signals['new_launches']) < 5:
                            signals['new_launches'].append({
                                'symbol': pair.get('baseToken', {}).get('symbol', 'N/A'),
                                'chain': pair.get('chainId', 'N/A'),
                                'address': pair.get('baseToken', {}).get('address', ''),
                                'age_hours': round(age_hours, 1),
                                'liquidity_usd': round(liquidity_usd),
                                'volume_24h': round(pair.get('volume', {}).get('h24', 0)),
                                'total_txns_24h': 0,  # Not available in search
                                'price_change_24h': pair.get('priceChange', {}).get('h24', 0),
                                'url': pair.get('url', '')
                            })
                
                # Volume spikes (check all pairs)
                volume_h24 = pair.get('volume', {}).get('h24', 0)
                volume_h6 = pair.get('volume', {}).get('h6', 0)
                
                if volume_h6 > 1000 and volume_h24 > 0:  # Just $1k volume
                    spike_ratio = (volume_h6 * 4) / volume_h24
                    
                    if spike_ratio > 1.1:  # Just 10% increase
                        spike_count += 1
                        if len(signals['volume_spikes']) < 5:
                            signals['volume_spikes'].append({
                                'symbol': pair.get('baseToken', {}).get('symbol', 'N/A'),
                                'chain': pair.get('chainId', 'N/A'),
                                'address': pair.get('baseToken', {}).get('address', ''),
                                'volume_spike_ratio': round(spike_ratio, 1),
                                'volume_6h': round(volume_h6),
                                'volume_24h': round(volume_h24),
                                'liquidity_usd': round(pair.get('liquidity', {}).get('usd', 0)),
                                'price_change_6h': pair.get('priceChange', {}).get('h6', 0),
                                'url': pair.get('url', '')
                            })
                            
        except Exception as e:
            print(f"Error processing pair: {e}")
    
    print(f"\nResults:")
    print(f"- New launches found: {new_count} (showing top 5)")
    print(f"- Volume spikes found: {spike_count} (showing top 5)")
    
    # Sort by best first
    signals['new_launches'] = sorted(signals['new_launches'], key=lambda x: x['volume_24h'], reverse=True)[:5]
    signals['volume_spikes'] = sorted(signals['volume_spikes'], key=lambda x: x['volume_spike_ratio'], reverse=True)[:5]
    
    return signals

if __name__ == "__main__":
    signals = get_dexscreener_signals_fixed()
    
    print("\n" + "="*60)
    print("SIGNALS FOUND:")
    print("="*60)
    
    print(f"\n🆕 New Launches: {len(signals['new_launches'])}")
    for token in signals['new_launches'][:2]:
        print(f"  ${token['symbol']} - {token['age_hours']}h old, ${token['liquidity_usd']:,} liquidity")
    
    print(f"\n📈 Volume Spikes: {len(signals['volume_spikes'])}")
    for token in signals['volume_spikes'][:2]:
        print(f"  ${token['symbol']} - {token['volume_spike_ratio']}x spike")