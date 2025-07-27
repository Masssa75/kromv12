import requests
import time
from datetime import datetime, timedelta
import json

def get_dexscreener_signals_improved():
    """Get comprehensive DexScreener signals for tokens worth researching"""
    signals = {
        'trending': [],
        'new_launches': [],
        'volume_spikes': [],
        'top_gainers': [],
        'boosted_tokens': [],
        'high_activity': []
    }
    
    all_tokens = {}  # Use dict to track unique tokens
    
    # 1. Get boosted tokens (both latest and top)
    print("Fetching boosted tokens...")
    try:
        # Latest boosted
        response = requests.get("https://api.dexscreener.com/token-boosts/latest/v1")
        if response.status_code == 200:
            boosts = response.json()[:30]  # Get more boosted tokens
            for boost in boosts:
                token_address = boost.get('tokenAddress')
                if token_address and token_address not in all_tokens:
                    all_tokens[token_address] = {'boost': boost, 'source': 'boosted_latest'}
        
        # Top boosted
        response = requests.get("https://api.dexscreener.com/token-boosts/top/v1")
        if response.status_code == 200:
            boosts = response.json()[:30]
            for boost in boosts:
                token_address = boost.get('tokenAddress')
                if token_address and token_address not in all_tokens:
                    all_tokens[token_address] = {'boost': boost, 'source': 'boosted_top'}
                    
    except Exception as e:
        print(f"Error fetching boosted tokens: {e}")
    
    # 2. Get token profiles (often has newer tokens)
    print("Fetching token profiles...")
    try:
        response = requests.get("https://api.dexscreener.com/token-profiles/latest/v1")
        if response.status_code == 200:
            profiles = response.json()[:50]
            for profile in profiles:
                token_address = profile.get('tokenAddress')
                if token_address and token_address not in all_tokens:
                    all_tokens[token_address] = {'profile': profile, 'source': 'profiles'}
    except Exception as e:
        print(f"Error fetching profiles: {e}")
    
    # 3. Search for various token categories
    print("Searching for tokens by category...")
    search_terms = [
        # Major chains/tokens
        'SOL', 'ETH', 'BNB', 'MATIC', 'AVAX', 'FTM', 'ARB',
        # Popular categories
        'MEME', 'AI', 'PEPE', 'DOGE', 'SHIB', 'FLOKI',
        # Trading pairs
        'USDC', 'USDT', 'WETH', 'WBNB', 'WSOL',
        # Trending topics
        'TRUMP', 'ELON', 'MOON', 'ROCKET', 'APE',
        # Chain specific
        'BASE', 'BLAST', 'ZKSYNC', 'LINEA', 'SCROLL'
    ]
    
    for term in search_terms:
        try:
            response = requests.get(f"https://api.dexscreener.com/latest/dex/search?q={term}")
            if response.status_code == 200:
                data = response.json()
                pairs = data.get('pairs', [])[:30]  # Get more from each search
                
                for pair in pairs:
                    token_address = pair.get('baseToken', {}).get('address')
                    if token_address and token_address not in all_tokens:
                        all_tokens[token_address] = {'pair': pair, 'source': f'search_{term}'}
                
                print(f"Found {len(pairs)} pairs for {term}")
            time.sleep(0.1)  # Rate limiting
        except Exception as e:
            print(f"Error searching {term}: {e}")
    
    # 4. Now fetch detailed pair data for all discovered tokens
    print(f"\nFetching detailed data for {len(all_tokens)} unique tokens...")
    tokens_with_data = []
    
    for i, (token_address, token_info) in enumerate(all_tokens.items()):
        if i % 10 == 0:
            print(f"Processing token {i+1}/{len(all_tokens)}...")
            
        try:
            # If we already have pair data from search, use it
            if 'pair' in token_info:
                pair = token_info['pair']
            else:
                # Otherwise fetch it
                response = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{token_address}")
                if response.status_code == 200:
                    pairs = response.json().get('pairs', [])
                    if pairs:
                        pair = pairs[0]  # Use the main pair
                    else:
                        continue
                else:
                    continue
            
            # Extract key metrics
            created_at = pair.get('pairCreatedAt')
            if created_at:
                age_hours = (time.time() * 1000 - created_at) / (1000 * 3600)
            else:
                age_hours = 9999  # Unknown age
            
            liquidity_usd = pair.get('liquidity', {}).get('usd', 0)
            volume_24h = pair.get('volume', {}).get('h24', 0)
            volume_6h = pair.get('volume', {}).get('h6', 0)
            volume_1h = pair.get('volume', {}).get('h1', 0)
            price_change_24h = pair.get('priceChange', {}).get('h24', 0)
            price_change_6h = pair.get('priceChange', {}).get('h6', 0)
            price_change_1h = pair.get('priceChange', {}).get('h1', 0)
            txns_24h = pair.get('txns', {}).get('h24', {})
            total_txns = txns_24h.get('buys', 0) + txns_24h.get('sells', 0)
            
            # Store token data
            token_data = {
                'symbol': pair.get('baseToken', {}).get('symbol', 'N/A'),
                'name': pair.get('baseToken', {}).get('name', ''),
                'chain': pair.get('chainId', 'N/A'),
                'address': token_address,
                'age_hours': round(age_hours, 1),
                'liquidity_usd': round(liquidity_usd),
                'volume_24h': round(volume_24h),
                'volume_6h': round(volume_6h),
                'volume_1h': round(volume_1h),
                'price_change_24h': price_change_24h,
                'price_change_6h': price_change_6h,
                'price_change_1h': price_change_1h,
                'total_txns_24h': total_txns,
                'url': pair.get('url', ''),
                'source': token_info.get('source', 'unknown'),
                'boost_amount': token_info.get('boost', {}).get('totalAmount', 0) if 'boost' in token_info else 0
            }
            
            tokens_with_data.append(token_data)
            
        except Exception as e:
            print(f"Error processing token {token_address}: {e}")
            
        time.sleep(0.05)  # Rate limiting
    
    # 5. Categorize tokens
    print(f"\nCategorizing {len(tokens_with_data)} tokens...")
    
    for token in tokens_with_data:
        # Skip tokens with very low liquidity (likely scams)
        if token['liquidity_usd'] < 1000:
            continue
            
        # New launches (< 24 hours, with decent liquidity)
        if token['age_hours'] < 24 and token['liquidity_usd'] > 2000:
            signals['new_launches'].append(token)
        
        # Trending (high volume relative to liquidity)
        if token['volume_24h'] > 0 and token['liquidity_usd'] > 0:
            volume_to_liq_ratio = token['volume_24h'] / token['liquidity_usd']
            if volume_to_liq_ratio > 0.5 and token['liquidity_usd'] > 5000:  # 50% daily volume
                signals['trending'].append(token)
        
        # Volume spikes
        if token['volume_6h'] > 0 and token['volume_24h'] > 0:
            projected_24h = token['volume_6h'] * 4
            spike_ratio = projected_24h / token['volume_24h']
            if spike_ratio > 1.5 and token['volume_6h'] > 5000:  # 50% spike
                token['volume_spike_ratio'] = round(spike_ratio, 1)
                signals['volume_spikes'].append(token)
        
        # Top gainers
        if token['price_change_6h'] > 50 and token['liquidity_usd'] > 3000:
            signals['top_gainers'].append(token)
        
        # Boosted tokens (that also have good metrics)
        if token['boost_amount'] > 0 and token['liquidity_usd'] > 10000:
            signals['boosted_tokens'].append(token)
        
        # High activity (lots of transactions)
        if token['total_txns_24h'] > 1000 and token['liquidity_usd'] > 5000:
            signals['high_activity'].append(token)
    
    # 6. Sort and limit results
    signals['new_launches'] = sorted(signals['new_launches'], key=lambda x: x['volume_24h'], reverse=True)[:20]
    signals['trending'] = sorted(signals['trending'], key=lambda x: x['volume_24h'], reverse=True)[:20]
    signals['volume_spikes'] = sorted(signals['volume_spikes'], key=lambda x: x.get('volume_spike_ratio', 0), reverse=True)[:20]
    signals['top_gainers'] = sorted(signals['top_gainers'], key=lambda x: x['price_change_6h'], reverse=True)[:20]
    signals['boosted_tokens'] = sorted(signals['boosted_tokens'], key=lambda x: x['boost_amount'], reverse=True)[:15]
    signals['high_activity'] = sorted(signals['high_activity'], key=lambda x: x['total_txns_24h'], reverse=True)[:15]
    
    # Print summary
    print("\n=== SUMMARY ===")
    print(f"Total unique tokens discovered: {len(all_tokens)}")
    print(f"Tokens with valid data: {len(tokens_with_data)}")
    print(f"New launches (<24h): {len(signals['new_launches'])}")
    print(f"Trending tokens: {len(signals['trending'])}")
    print(f"Volume spikes: {len(signals['volume_spikes'])}")
    print(f"Top gainers: {len(signals['top_gainers'])}")
    print(f"Boosted tokens: {len(signals['boosted_tokens'])}")
    print(f"High activity: {len(signals['high_activity'])}")
    
    total_signals = sum(len(category) for category in signals.values())
    print(f"\nTotal signals generated: {total_signals}")
    
    return {
        'success': True,
        'timestamp': datetime.now().isoformat(),
        'signals': signals,
        'summary': {
            'new_launches': len(signals['new_launches']),
            'trending': len(signals['trending']),
            'volume_spikes': len(signals['volume_spikes']),
            'top_gainers': len(signals['top_gainers']),
            'boosted_tokens': len(signals['boosted_tokens']),
            'high_activity': len(signals['high_activity']),
            'total': total_signals
        }
    }

# Test the improved function
if __name__ == "__main__":
    print("Testing improved DexScreener signals...")
    result = get_dexscreener_signals_improved()
    
    # Save to file for inspection
    with open('improved_signals.json', 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\nResults saved to improved_signals.json")
    print(f"Total signals: {result['summary']['total']}")