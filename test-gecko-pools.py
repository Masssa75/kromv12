import requests
import json

print("=== TESTING GECKOTERMINAL POOLS ===")

# Test with EASY token that showed 4993% difference
test_tokens = [
    {"ticker": "EASY", "address": "0x7703dC16c4B43f8ff039817c4E87f2DD6a9a31Ed", "network": "ethereum"},
    {"ticker": "LOA", "address": "0x2F0c6e147974BfbF7Da557b88643D74C324053A2", "network": "ethereum"}
]

for token in test_tokens:
    print(f"\nChecking {token['ticker']}...")
    
    # Map network name
    network_map = {'ethereum': 'eth', 'solana': 'solana', 'bsc': 'bsc'}
    api_network = network_map.get(token['network'], token['network'])
    
    response = requests.get(f"https://api.geckoterminal.com/api/v2/networks/{api_network}/tokens/{token['address']}/pools")
    
    if response.status_code == 200:
        data = response.json()
        pools = data.get('data', [])
        
        print(f"Found {len(pools)} pools")
        
        # Show all pools
        for i, pool in enumerate(pools[:5]):  # Show first 5
            attrs = pool['attributes']
            print(f"\n  Pool {i+1}:")
            print(f"    Price: ${attrs.get('token_price_usd')}")
            print(f"    Liquidity: ${attrs.get('reserve_in_usd')}")
            print(f"    Pool name: {attrs.get('name')}")
            print(f"    DEX: {attrs.get('dex_id')}")
            print(f"    Pool address: {attrs.get('address', 'N/A')[:20]}...")
        
        # Show which price would be selected
        if pools:
            # Old logic (highest price)
            highest_price = 0
            for pool in pools:
                price = float(pool['attributes'].get('token_price_usd', 0))
                if price > highest_price:
                    highest_price = price
            
            # New logic (highest liquidity)
            sorted_pools = sorted(pools, key=lambda p: float(p['attributes'].get('reserve_in_usd', 0)), reverse=True)
            best_liquidity_price = float(sorted_pools[0]['attributes'].get('token_price_usd', 0))
            
            print(f"\n  OLD LOGIC (highest price): ${highest_price}")
            print(f"  NEW LOGIC (highest liquidity): ${best_liquidity_price}")
            print(f"  Difference: {abs(highest_price - best_liquidity_price) / best_liquidity_price * 100:.1f}%")
