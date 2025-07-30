import requests
import json

print('=== TESTING GECKOTERMINAL POOL SELECTION FIX ===')

# Test with LOA token that showed 3278% difference
test_token = {
    'ticker': 'LOA',
    'address': '0x2F0c6e147974BfbF7Da557b88643D74C324053A2',
    'network': 'ethereum'
}

print(f"\nChecking {test_token['ticker']}...")

# Try DexScreener first to get correct price
dex_response = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{test_token['address']}")
correct_price = None

if dex_response.status_code == 200:
    dex_data = dex_response.json()
    if dex_data.get('pairs') and len(dex_data['pairs']) > 0:
        correct_price = float(dex_data['pairs'][0]['priceUsd'])
        print(f"DexScreener price (correct): ${correct_price}")

# Now test GeckoTerminal
network_map = {'ethereum': 'eth', 'solana': 'solana', 'bsc': 'bsc'}
api_network = network_map.get(test_token['network'], test_token['network'])

response = requests.get(f"https://api.geckoterminal.com/api/v2/networks/{api_network}/tokens/{test_token['address']}/pools")

if response.status_code == 200:
    data = response.json()
    pools = data.get('data', [])
    
    print(f'\nGeckoTerminal found {len(pools)} pools')
    
    if pools:
        # Show all pools
        print('\nAll Pools:')
        for i, pool in enumerate(pools):
            attrs = pool['attributes']
            price = float(attrs.get('token_price_usd', 0))
            liquidity = float(attrs.get('reserve_in_usd', 0))
            print(f'  Pool {i+1}:')
            print(f"    Price: ${price}")
            print(f"    Liquidity: ${liquidity:,.0f}")
            print(f"    DEX: {attrs.get('dex_id')}")
            print(f"    Pool name: {attrs.get('name')}")
        
        # OLD LOGIC - Find highest price
        highest_price = 0
        highest_price_pool = None
        for pool in pools:
            price = float(pool['attributes'].get('token_price_usd', 0))
            if price > highest_price:
                highest_price = price
                highest_price_pool = pool
        
        # NEW LOGIC - Sort by liquidity
        sorted_pools = sorted(pools, key=lambda p: float(p['attributes'].get('reserve_in_usd', 0)), reverse=True)
        best_pool = sorted_pools[0]
        best_price = float(best_pool['attributes'].get('token_price_usd', 0))
        
        print(f'\n=== RESULTS ===')
        if correct_price:
            print(f"Correct price (DexScreener): ${correct_price}")
        print(f'OLD LOGIC (highest price): ${highest_price}')
        print(f"  From pool: {highest_price_pool['attributes'].get('name')}")
        print(f'NEW LOGIC (highest liquidity): ${best_price}')
        print(f"  From pool: {best_pool['attributes'].get('name')}")
        
        if correct_price:
            old_error = abs(highest_price - correct_price) / correct_price * 100
            new_error = abs(best_price - correct_price) / correct_price * 100
            
            print(f'\nOLD LOGIC error: {old_error:.0f}%')
            print(f'NEW LOGIC error: {new_error:.0f}%')
            
            if new_error < old_error:
                print(f'\n✅ NEW LOGIC IS BETTER! (Error reduced from {old_error:.0f}% to {new_error:.0f}%)')
            else:
                print(f'\n❌ Old logic was better')
else:
    print(f"GeckoTerminal API error: {response.status_code}")