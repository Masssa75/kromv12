import requests
import json
from datetime import datetime

# Token address and timestamp from the user's screenshot
token_address = '3ZuM2k3BmPr3anKcq7Kvwm6YAE44YGg4DwGr88BCbonk'
# July 26 10:08 PM (Thai time is UTC+7)
timestamp = datetime(2025, 7, 26, 22, 8, 0).timestamp() - (7 * 3600)  # Convert to UTC

print(f'Token: {token_address}')
print(f'Timestamp: {int(timestamp)} ({datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S UTC")})')

# First, let's get the token info from GeckoTerminal
url = f'https://api.geckoterminal.com/api/v2/networks/solana/tokens/{token_address}'
response = requests.get(url)
if response.ok:
    data = response.json()
    attrs = data['data']['attributes']
    print(f'\nToken Info:')
    print(f'Name: {attrs.get("name")}')
    print(f'Symbol: {attrs.get("symbol")}')
    print(f'Current Price: ${attrs.get("price_usd")}')
    print(f'FDV: ${attrs.get("fdv_usd")}')
    
# Get pools for this token
pools_url = f'https://api.geckoterminal.com/api/v2/networks/solana/tokens/{token_address}/pools'
response = requests.get(pools_url)
if response.ok:
    data = response.json()
    pools = data['data']
    print(f'\nFound {len(pools)} pools')
    if pools:
        # Get the most liquid pool
        pool = pools[0]
        pool_address = pool['attributes']['address']
        print(f'Using pool: {pool_address}')
        print(f'Pool liquidity: ${pool["attributes"].get("reserve_in_usd")}')
        
        # Get OHLCV data - try different timeframes
        for timeframe in ['minute', 'hour', 'day']:
            print(f'\n--- Trying {timeframe} timeframe ---')
            ohlcv_url = f'https://api.geckoterminal.com/api/v2/networks/solana/pools/{pool_address}/ohlcv/{timeframe}?limit=1000&currency=usd'
            response = requests.get(ohlcv_url)
            if response.ok:
                data = response.json()
                ohlcv_list = data['data']['attributes']['ohlcv_list']
                print(f'Got {len(ohlcv_list)} {timeframe} candles')
                
                # Show recent prices
                if ohlcv_list:
                    print(f'\nRecent prices (last 10 candles):')
                    for i, candle in enumerate(ohlcv_list[:10]):
                        candle_time = datetime.fromtimestamp(candle[0])
                        # candle format: [timestamp, open, high, low, close, volume]
                        print(f'{candle_time.strftime("%Y-%m-%d %H:%M")} - O: ${candle[1]:.6f}, H: ${candle[2]:.6f}, L: ${candle[3]:.6f}, C: ${candle[4]:.6f}')
                    
                    # Find the highest price in all data
                    max_price = max(candle[2] for candle in ohlcv_list)  # high price
                    max_candle = next(c for c in ohlcv_list if c[2] == max_price)
                    max_time = datetime.fromtimestamp(max_candle[0])
                    print(f'\nAll-time high in this dataset: ${max_price:.6f} at {max_time.strftime("%Y-%m-%d %H:%M")}')