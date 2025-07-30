import requests
import json
import time

print('=== TESTING WITH ACTIVE TOKEN (PEPE) ===')

# Test with PEPE - a well-known token with multiple pools
test_token = {
    'ticker': 'PEPE',
    'address': '0x6982508145454Ce325dDbE47a25d4ec3d2311933',
    'network': 'ethereum'
}

print(f"\nChecking {test_token['ticker']}...")

# Get correct price from DexScreener
dex_response = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{test_token['address']}")
correct_price = None

if dex_response.status_code == 200:
    dex_data = dex_response.json()
    if dex_data.get('pairs') and len(dex_data['pairs']) > 0:
        # DexScreener already sorts by liquidity/volume
        correct_price = float(dex_data['pairs'][0]['priceUsd'])
        print(f"DexScreener price: ${correct_price:.10f}")

# Test GeckoTerminal
time.sleep(0.5)  # Rate limit
network_map = {'ethereum': 'eth', 'solana': 'solana', 'bsc': 'bsc'}
api_network = network_map.get(test_token['network'], test_token['network'])

response = requests.get(f"https://api.geckoterminal.com/api/v2/networks/{api_network}/tokens/{test_token['address']}/pools")

if response.status_code == 200:
    data = response.json()
    pools = data.get('data', [])
    
    print(f'\nGeckoTerminal found {len(pools)} pools')
    
    if pools:
        # Show pools with different prices
        unique_prices = {}
        for pool in pools:
            price = float(pool['attributes'].get('token_price_usd', 0))
            liquidity = float(pool['attributes'].get('reserve_in_usd', 0))
            if price > 0:
                if price not in unique_prices or liquidity > unique_prices[price]['liquidity']:
                    unique_prices[price] = {
                        'liquidity': liquidity,
                        'name': pool['attributes'].get('name'),
                        'dex': pool['attributes'].get('dex_id')
                    }
        
        print(f'\nFound {len(unique_prices)} unique prices:')
        for price, info in sorted(unique_prices.items(), reverse=True)[:5]:
            print(f'  ${price:.10f} (liquidity: ${info["liquidity"]:,.0f}) on {info["dex"]}')
        
        # Compare OLD vs NEW logic
        highest_price_pool = max(pools, key=lambda p: float(p['attributes'].get('token_price_usd', 0)))
        highest_liquidity_pool = max(pools, key=lambda p: float(p['attributes'].get('reserve_in_usd', 0)))
        
        old_price = float(highest_price_pool['attributes'].get('token_price_usd', 0))
        new_price = float(highest_liquidity_pool['attributes'].get('token_price_usd', 0))
        
        print(f'\n=== RESULTS ===')
        print(f'OLD LOGIC (highest price): ${old_price:.10f}')
        print(f'  From pool: {highest_price_pool["attributes"].get("name")}')
        print(f'  Liquidity: ${float(highest_price_pool["attributes"].get("reserve_in_usd", 0)):,.0f}')
        
        print(f'\nNEW LOGIC (highest liquidity): ${new_price:.10f}')
        print(f'  From pool: {highest_liquidity_pool["attributes"].get("name")}')
        print(f'  Liquidity: ${float(highest_liquidity_pool["attributes"].get("reserve_in_usd", 0)):,.0f}')
        
        if correct_price:
            old_diff = abs(old_price - correct_price) / correct_price * 100
            new_diff = abs(new_price - correct_price) / correct_price * 100
            
            print(f'\nAccuracy comparison:')
            print(f'DexScreener (reference): ${correct_price:.10f}')
            print(f'OLD LOGIC diff: {old_diff:.2f}%')
            print(f'NEW LOGIC diff: {new_diff:.2f}%')
            
            if new_diff < old_diff:
                print(f'\n✅ NEW LOGIC IS BETTER!')
            elif new_diff == old_diff:
                print(f'\n✓ Both logics give same result (good in this case)')
            else:
                print(f'\n⚠️ Old logic was closer')