#!/usr/bin/env python3
"""
Fetch the price of Solana token 3ZuM2k3BmPr3anKcq7Kvwm6YAE44YGg4DwGr88BCbonk
at July 26 10:08pm using the GeckoTerminal API
"""

import urllib.request
import urllib.parse
import json
from datetime import datetime, timezone
import time

# Token details
TOKEN_ADDRESS = "3ZuM2k3BmPr3anKcq7Kvwm6YAE44YGg4DwGr88BCbonk"
NETWORK = "solana"

# Target timestamp: July 26, 2025 10:08 PM (assuming current year is 2025 based on the system date)
# Converting to UTC timestamp
target_datetime = datetime(2025, 7, 26, 22, 8, 0)  # 10:08 PM
target_timestamp = int(target_datetime.timestamp())

print(f"Token Address: {TOKEN_ADDRESS}")
print(f"Network: {NETWORK}")
print(f"Target Time: {target_datetime} ({target_timestamp})")
print("=" * 80)

# GeckoTerminal API base URL
BASE_URL = "https://api.geckoterminal.com/api/v2"

def get_token_info():
    """Get current token information"""
    url = f"{BASE_URL}/networks/{NETWORK}/tokens/{TOKEN_ADDRESS}"
    print(f"\nFetching token info from: {url}")
    
    try:
        response = urllib.request.urlopen(url)
        if response.status == 200:
            data = json.loads(response.read().decode())
            if 'data' in data and 'attributes' in data['data']:
                attrs = data['data']['attributes']
                print(f"\nToken Found!")
                print(f"Name: {attrs.get('name', 'N/A')}")
                print(f"Symbol: {attrs.get('symbol', 'N/A')}")
                print(f"Current Price: ${attrs.get('price_usd', 'N/A')}")
                print(f"Market Cap: ${attrs.get('market_cap_usd', 'N/A')}")
                print(f"FDV: ${attrs.get('fdv_usd', 'N/A')}")
                return attrs
            else:
                print("Token data not found in response")
                return None
        else:
            print(f"Failed to fetch token info: Status {response.status}")
            return None
    except Exception as e:
        print(f"Error fetching token info: {e}")
        return None

def get_token_pools():
    """Get pools for the token"""
    url = f"{BASE_URL}/networks/{NETWORK}/tokens/{TOKEN_ADDRESS}/pools"
    print(f"\nFetching token pools from: {url}")
    
    try:
        response = urllib.request.urlopen(url)
        if response.status == 200:
            data = json.loads(response.read().decode())
            pools = data.get('data', [])
            print(f"\nFound {len(pools)} pools")
            
            if pools:
                # Sort by liquidity
                sorted_pools = sorted(pools, 
                    key=lambda p: float(p['attributes'].get('reserve_in_usd', '0')), 
                    reverse=True)
                
                main_pool = sorted_pools[0]
                pool_attrs = main_pool['attributes']
                print(f"\nMain Pool:")
                print(f"Pool Address: {pool_attrs.get('address', 'N/A')}")
                print(f"Liquidity: ${pool_attrs.get('reserve_in_usd', 'N/A')}")
                print(f"Base Token Price: ${pool_attrs.get('base_token_price_usd', 'N/A')}")
                
                # Handle nested volume data
                volume_data = pool_attrs.get('volume_usd', {})
                if isinstance(volume_data, dict):
                    volume_24h = volume_data.get('h24', 'N/A')
                else:
                    volume_24h = 'N/A'
                print(f"24h Volume: ${volume_24h}")
                
                return sorted_pools
            return []
        else:
            print(f"Failed to fetch pools: Status {response.status}")
            return []
    except Exception as e:
        print(f"Error fetching pools: {e}")
        return []

def get_historical_price(pool_address, timestamp):
    """Get historical price data for a pool"""
    timeframes = [
        ('day', 86400, 30),
        ('hour', 3600, 168),
        ('minute', 300, 288)
    ]
    
    for interval, before_offset, limit in timeframes:
        # We want data from BEFORE the timestamp
        params = {
            'before_timestamp': timestamp,
            'limit': limit,
            'currency': 'usd'
        }
        
        url = f"{BASE_URL}/networks/{NETWORK}/pools/{pool_address}/ohlcv/{interval}"
        full_url = url + '?' + urllib.parse.urlencode(params)
        
        print(f"\nTrying {interval} timeframe...")
        print(f"URL: {full_url}")
        
        try:
            response = urllib.request.urlopen(full_url)
            if response.status == 200:
                data = json.loads(response.read().decode())
                ohlcv_list = data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
                
                if ohlcv_list:
                    print(f"Found {len(ohlcv_list)} {interval} candles")
                    
                    # Find closest price to target timestamp
                    closest_price = None
                    closest_diff = float('inf')
                    closest_candle = None
                    
                    for candle in ohlcv_list:
                        # candle format: [timestamp, open, high, low, close, volume]
                        candle_timestamp = candle[0]
                        diff = abs(candle_timestamp - timestamp)
                        
                        if diff < closest_diff:
                            closest_diff = diff
                            closest_price = candle[4]  # close price
                            closest_candle = candle
                    
                    if closest_price is not None:
                        candle_time = datetime.fromtimestamp(closest_candle[0])
                        diff_minutes = closest_diff / 60
                        print(f"\nFound historical price!")
                        print(f"Price: ${closest_price}")
                        print(f"Candle Time: {candle_time}")
                        print(f"Time Difference: {diff_minutes:.1f} minutes")
                        print(f"OHLC: Open=${closest_candle[1]}, High=${closest_candle[2]}, Low=${closest_candle[3]}, Close=${closest_candle[4]}")
                        print(f"Volume: ${closest_candle[5]}")
                        return {
                            'price': closest_price,
                            'timestamp': closest_candle[0],
                            'candle_time': candle_time,
                            'diff_minutes': diff_minutes,
                            'ohlcv': closest_candle
                        }
                else:
                    print(f"No {interval} data available")
            else:
                print(f"Failed to fetch {interval} data: Status {response.status}")
                
            # Small delay between requests
            time.sleep(0.1)
            
        except Exception as e:
            print(f"Error fetching {interval} data: {e}")
    
    return None

def main():
    # Step 1: Get token info
    token_info = get_token_info()
    if not token_info:
        print("\nToken not found on GeckoTerminal")
        return
    
    # Step 2: Get pools
    pools = get_token_pools()
    if not pools:
        print("\nNo pools found for this token")
        return
    
    # Step 3: Get historical price from the main pool
    main_pool = pools[0]
    pool_address = main_pool['attributes']['address']
    
    print(f"\n{'=' * 80}")
    print(f"Fetching historical price at {target_datetime}")
    print(f"{'=' * 80}")
    
    historical_data = get_historical_price(pool_address, target_timestamp)
    
    if historical_data:
        print(f"\n{'=' * 80}")
        print("SUMMARY")
        print(f"{'=' * 80}")
        print(f"Token: {token_info.get('symbol', 'N/A')} ({token_info.get('name', 'N/A')})")
        print(f"Contract: {TOKEN_ADDRESS}")
        print(f"Network: Solana")
        print(f"Target Time: July 26, 2025 10:08 PM")
        print(f"Price at Target Time: ${historical_data['price']}")
        print(f"Current Price: ${token_info.get('price_usd', 'N/A')}")
        
        # Calculate ROI if both prices available
        if token_info.get('price_usd') and historical_data['price']:
            current = float(token_info['price_usd'])
            historical = float(historical_data['price'])
            roi = ((current - historical) / historical) * 100
            print(f"Price Change: {roi:+.2f}%")
    else:
        print("\nCould not find historical price data for the specified time")

if __name__ == "__main__":
    main()