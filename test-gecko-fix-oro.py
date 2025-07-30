import requests
import json

print('=== TESTING GECKOTERMINAL POOL SELECTION FIX WITH ORO ===')

# ORO token showing 24592088220958% ROI (clearly wrong)
test_token = {
    'ticker': 'ORO',
    'address': '0xB33eB2d8ea7DC5830dF43936A3BA3c2FDaa95753',
    'network': 'ethereum',
    'db_price': 9467.9539651073,  # Inflated price in DB
    'entry_price': 3.85e-08
}

print(f"\nChecking {test_token['ticker']}...")
print(f"Entry price: ${test_token['entry_price']}")
print(f"DB current price: ${test_token['db_price']} (WRONG - gives {(test_token['db_price']/test_token['entry_price'] - 1)*100:.0f}% ROI)")

# Try DexScreener first to get correct price
dex_response = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{test_token['address']}")
correct_price = None

if dex_response.status_code == 200:
    dex_data = dex_response.json()
    if dex_data.get('pairs') and len(dex_data['pairs']) > 0:
        correct_price = float(dex_data['pairs'][0]['priceUsd'])
        correct_roi = ((correct_price - test_token['entry_price']) / test_token['entry_price']) * 100
        print(f"\nDexScreener price (correct): ${correct_price}")
        print(f"Correct ROI should be: {correct_roi:.1f}%")
    else:
        print("\nDexScreener: No pairs found")

# Now test GeckoTerminal
network_map = {'ethereum': 'eth', 'solana': 'solana', 'bsc': 'bsc'}
api_network = network_map.get(test_token['network'], test_token['network'])

response = requests.get(f"https://api.geckoterminal.com/api/v2/networks/{api_network}/tokens/{test_token['address']}/pools")

if response.status_code == 200:
    data = response.json()
    pools = data.get('data', [])
    
    print(f'\nGeckoTerminal found {len(pools)} pools')
    
    if pools:
        # Show top 5 pools by price and liquidity
        print('\nTop pools by PRICE (OLD LOGIC):')
        sorted_by_price = sorted(pools, key=lambda p: float(p['attributes'].get('token_price_usd', 0)), reverse=True)
        for i, pool in enumerate(sorted_by_price[:3]):
            attrs = pool['attributes']
            price = float(attrs.get('token_price_usd', 0))
            liquidity = float(attrs.get('reserve_in_usd', 0))
            print(f'  {i+1}. ${price} (liquidity: ${liquidity:,.0f}) - {attrs.get("name")[:50]}')
        
        print('\nTop pools by LIQUIDITY (NEW LOGIC):')
        sorted_by_liquidity = sorted(pools, key=lambda p: float(p['attributes'].get('reserve_in_usd', 0)), reverse=True)
        for i, pool in enumerate(sorted_by_liquidity[:3]):
            attrs = pool['attributes']
            price = float(attrs.get('token_price_usd', 0))
            liquidity = float(attrs.get('reserve_in_usd', 0))
            print(f'  {i+1}. ${price} (liquidity: ${liquidity:,.0f}) - {attrs.get("name")[:50]}')
        
        # Compare results
        old_price = float(sorted_by_price[0]['attributes'].get('token_price_usd', 0))
        new_price = float(sorted_by_liquidity[0]['attributes'].get('token_price_usd', 0))
        
        print(f'\n=== RESULTS ===')
        print(f'OLD LOGIC picks: ${old_price}')
        print(f'NEW LOGIC picks: ${new_price}')
        
        if correct_price:
            old_error = abs(old_price - correct_price) / correct_price * 100
            new_error = abs(new_price - correct_price) / correct_price * 100
            
            print(f'\nCorrect price: ${correct_price}')
            print(f'OLD LOGIC error: {old_error:.0f}%')
            print(f'NEW LOGIC error: {new_error:.0f}%')
            
            if new_error < old_error:
                print(f'\n✅ NEW LOGIC IS MUCH BETTER!')
                print(f'Error reduced from {old_error:.0f}% to {new_error:.0f}%')
else:
    print(f"GeckoTerminal API error: {response.status_code}")