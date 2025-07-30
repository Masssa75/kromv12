import requests
import json

print('=== TESTING GECKOTERMINAL POOL SELECTION FIX ===')

# Test EASY token that had wrong price
test_token = {
    'ticker': 'EASY',
    'address': '0x7703dC16c4B43f8ff039817c4E87f2DD6a9a31Ed',
    'network': 'ethereum',
    'db_price': 0.002606,  # Wrong price in DB
    'expected_price': 0.00004996  # Approximate correct price
}

print(f"\nChecking {test_token['ticker']}...")

# Map network
network_map = {'ethereum': 'eth', 'solana': 'solana', 'bsc': 'bsc'}
api_network = network_map.get(test_token['network'], test_token['network'])

response = requests.get(f"https://api.geckoterminal.com/api/v2/networks/{api_network}/tokens/{test_token['address']}/pools")

if response.status_code == 200:
    data = response.json()
    pools = data.get('data', [])
    
    print(f'Found {len(pools)} pools')
    
    if pools:
        # Show first 3 pools
        print('\nPools (unsorted):')
        for i, pool in enumerate(pools[:3]):
            attrs = pool['attributes']
            print(f'  Pool {i+1}:')
            print(f"    Price: ${attrs.get('token_price_usd')}")
            print(f"    Liquidity: ${attrs.get('reserve_in_usd')}")
            print(f"    DEX: {attrs.get('dex_id')}")
        
        # OLD LOGIC - Find highest price
        highest_price = 0
        highest_price_liquidity = 0
        for pool in pools:
            price = float(pool['attributes'].get('token_price_usd', 0))
            if price > highest_price:
                highest_price = price
                highest_price_liquidity = float(pool['attributes'].get('reserve_in_usd', 0))
        
        # NEW LOGIC - Sort by liquidity
        sorted_pools = sorted(pools, key=lambda p: float(p['attributes'].get('reserve_in_usd', 0)), reverse=True)
        best_pool = sorted_pools[0]
        best_price = float(best_pool['attributes'].get('token_price_usd', 0))
        best_liquidity = float(best_pool['attributes'].get('reserve_in_usd', 0))
        
        print(f'\n=== RESULTS ===')
        print(f"DB has: ${test_token['db_price']} (WRONG)")
        print(f'OLD LOGIC (highest price): ${highest_price} (liquidity: ${highest_price_liquidity:,.0f})')
        print(f'NEW LOGIC (highest liquidity): ${best_price} (liquidity: ${best_liquidity:,.0f})')
        print(f"Expected correct price: ~${test_token['expected_price']}")
        
        # Check if new logic gives better result
        old_error = abs(highest_price - test_token['expected_price']) / test_token['expected_price'] * 100
        new_error = abs(best_price - test_token['expected_price']) / test_token['expected_price'] * 100
        
        print(f'\nOLD LOGIC error: {old_error:.0f}%')
        print(f'NEW LOGIC error: {new_error:.0f}%')
        
        if new_error < 50:
            print(f'\n✅ NEW LOGIC GIVES CORRECT PRICE!')
        else:
            print(f'\n⚠️  New price still seems off, but better than old logic' if new_error < old_error else '\n❌ New logic not better')