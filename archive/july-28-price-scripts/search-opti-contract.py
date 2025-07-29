#!/usr/bin/env python3
import json
import urllib.request

# Search for $OPTI pools by contract address
contract = '0x05E651Fe74f82598f52Da6C5761C02b7a8f56fCa'
krom_pool = '0xd23EA6834ea57A65797303AECaDF74eDff9FA095'

url = f'https://api.geckoterminal.com/api/v2/networks/ethereum/tokens/{contract}/pools'
print(f'Searching $OPTI by contract address:')
print(f'URL: {url}')
print()

req = urllib.request.Request(url)
req.add_header('User-Agent', 'Mozilla/5.0')

try:
    response = urllib.request.urlopen(req)
    data = json.loads(response.read().decode())
    pools = data.get('data', [])
    
    print(f'✅ Found {len(pools)} pools for $OPTI!')
    print()
    
    # Sort by liquidity
    sorted_pools = sorted(pools, key=lambda p: float(p['attributes'].get('reserve_in_usd', '0')), reverse=True)
    
    krom_pool_found = False
    
    for i, pool in enumerate(sorted_pools[:10]):  # Show top 10
        attrs = pool['attributes']
        pool_addr = attrs['address']
        liquidity = float(attrs.get('reserve_in_usd', '0'))
        price = attrs.get('base_token_price_usd')
        name = attrs.get('name', 'Unknown')
        
        print(f'Pool {i+1}: {pool_addr}')
        print(f'  Name: {name}')
        print(f'  Liquidity: ${liquidity:,.2f}')
        print(f'  Price: ${float(price) if price else 0:.8f}')
        
        if pool_addr.lower() == krom_pool.lower():
            print('  🎯 *** THIS IS KROM\'S POOL - SHOULD WORK! ***')
            krom_pool_found = True
        print()
    
    print(f'{"="*60}')
    if krom_pool_found:
        print('✅ KROM\'s pool address IS CORRECT!')
        print('❌ The issue is that this pool returns 404 when accessed directly')
        print(f'🔍 KROM pool: {krom_pool}')
    else:
        print('❌ KROM\'s pool address is NOT in the list!')
        print('💡 KROM might be using wrong/outdated pool address')
        print(f'🔍 KROM pool: {krom_pool}')
        print(f'💡 Best pool to use: {sorted_pools[0]["attributes"]["address"]}')
        
except Exception as e:
    print(f'❌ Error: {e}')