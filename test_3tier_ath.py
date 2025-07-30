import requests
from datetime import datetime, timedelta
import time

def get_ohlcv_data(network, pool_address, timeframe, limit=1000, before_timestamp=None):
    """Fetch OHLCV data from GeckoTerminal"""
    url = f"https://api.geckoterminal.com/api/v2/networks/{network}/pools/{pool_address}/ohlcv/{timeframe}"
    params = {'aggregate': 1, 'limit': limit}
    if before_timestamp:
        params['before_timestamp'] = before_timestamp
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if 'data' in data and 'attributes' in data['data']:
            return data['data']['attributes']['ohlcv_list']
        return []
    except Exception as e:
        print(f"Error fetching {timeframe} data: {e}")
        return []

def find_ath_3tier(network, pool_address, call_timestamp, ticker, group, price_at_call):
    """3-tier approach: daily -> hourly -> minute"""
    
    print(f"\n{'='*60}")
    print(f"🔍 3-TIER ATH ANALYSIS: {ticker}")
    print(f"Group: {group}")
    print(f"Network: {network.upper()}")
    print(f"Entry: ${price_at_call:.12f}")
    print(f"Call: {datetime.fromtimestamp(call_timestamp).strftime('%Y-%m-%d %H:%M')}")
    
    # TIER 1: Daily candles
    print(f"\n📅 TIER 1: Fetching daily candles...")
    daily_candles = get_ohlcv_data(network, pool_address, 'day', limit=1000)
    
    if not daily_candles:
        print("❌ No daily data available")
        return None
    
    # Find highest daily candle after call
    daily_highs = []
    for candle in daily_candles:
        if candle[0] >= call_timestamp and candle[2]:
            daily_highs.append({
                'timestamp': candle[0],
                'date': datetime.fromtimestamp(candle[0]).strftime('%Y-%m-%d'),
                'high': float(candle[2])
            })
    
    if not daily_highs:
        print("❌ No data after call date")
        return None
    
    daily_highs.sort(key=lambda x: x['high'], reverse=True)
    daily_ath = daily_highs[0]
    print(f"   Daily ATH: ${daily_ath['high']:.12f} on {daily_ath['date']}")
    
    # TIER 2: Hourly candles around ATH day
    print(f"\n🕐 TIER 2: Zooming into hourly candles...")
    # Get 72 hours before and after the ATH day
    before_ts = daily_ath['timestamp'] + (3 * 24 * 3600)  # 3 days after
    hourly_candles = get_ohlcv_data(network, pool_address, 'hour', limit=168, before_timestamp=before_ts)
    
    hourly_highs = []
    for candle in hourly_candles:
        # Only look at candles around the ATH day (±1 day)
        if abs(candle[0] - daily_ath['timestamp']) <= 86400 and candle[2]:
            hourly_highs.append({
                'timestamp': candle[0],
                'datetime': datetime.fromtimestamp(candle[0]).strftime('%Y-%m-%d %H:%M'),
                'high': float(candle[2])
            })
    
    if hourly_highs:
        hourly_highs.sort(key=lambda x: x['high'], reverse=True)
        hourly_ath = hourly_highs[0]
        print(f"   Hourly ATH: ${hourly_ath['high']:.12f} at {hourly_ath['datetime']}")
        
        # TIER 3: Minute candles around ATH hour
        print(f"\n⏱️  TIER 3: Zooming into minute candles...")
        # Get 2 hours before and after the ATH hour
        before_ts = hourly_ath['timestamp'] + (2 * 3600)  # 2 hours after
        minute_candles = get_ohlcv_data(network, pool_address, 'minute', limit=240, before_timestamp=before_ts)
        
        minute_data = []
        for candle in minute_candles:
            # Only look at candles around the ATH hour (±1 hour)
            if abs(candle[0] - hourly_ath['timestamp']) <= 3600 and candle[2] and candle[4]:
                minute_data.append({
                    'timestamp': candle[0],
                    'datetime': datetime.fromtimestamp(candle[0]).strftime('%Y-%m-%d %H:%M'),
                    'high': float(candle[2]),
                    'close': float(candle[4])  # We want the close\!
                })
        
        if minute_data:
            # Find the minute with highest high
            minute_data.sort(key=lambda x: x['high'], reverse=True)
            minute_ath = minute_data[0]
            
            # Calculate ROIs
            ath_high_roi = ((minute_ath['high'] - price_at_call) / price_at_call) * 100
            ath_close_roi = ((minute_ath['close'] - price_at_call) / price_at_call) * 100
            
            print(f"\n✅ FINAL ATH RESULTS:")
            print(f"   Peak Wick: ${minute_ath['high']:.12f} (ROI: {ath_high_roi:,.1f}%)")
            print(f"   Close Price: ${minute_ath['close']:.12f} (ROI: {ath_close_roi:,.1f}%)")
            print(f"   Time: {minute_ath['datetime']}")
            print(f"   Multiplier: {ath_close_roi/100 + 1:.1f}x")
            
            return {
                'ticker': ticker,
                'group': group,
                'ath_high': minute_ath['high'],
                'ath_close': minute_ath['close'],
                'ath_timestamp': minute_ath['timestamp'],
                'ath_datetime': minute_ath['datetime'],
                'high_roi': ath_high_roi,
                'close_roi': ath_close_roi
            }
        else:
            print("❌ No minute data available")
    else:
        print("❌ No hourly data available")
    
    return None

# Test cases
test_tokens = [
    {
        'ticker': 'BOOCHIE',
        'network': 'eth',
        'group': 'TopCallersChannel',
        'pool_address': '0x9392a42AbE7E8131E0956De4F8A0413f2a0e52BF',
        'call_timestamp': 1747688939,
        'price_at_call': 8E-10
    },
    {
        'ticker': 'KIRBY',
        'network': 'solana',
        'group': 'TopCallersChannel', 
        'pool_address': 'BSfB8FmXfjGDjuHR4aRYVfQ4JP6RvzDGZuPWfMAcZpJe',
        'call_timestamp': 1750873514,
        'price_at_call': 0.0014816853
    },
    {
        'ticker': 'BOOCHIE',
        'network': 'solana',
        'group': 'Unknown',
        'pool_address': '3YVbTqHctR7SKCfdYSAJJACriMTfi5AC4uVtUcvCTtdY',
        'call_timestamp': 1747738968,
        'price_at_call': 0.0001078409
    }
]

# Run tests with delay to respect rate limits
results = []
for token in test_tokens:
    result = find_ath_3tier(
        token['network'], 
        token['pool_address'],
        token['call_timestamp'],
        token['ticker'],
        token['group'],
        token['price_at_call']
    )
    if result:
        results.append(result)
    time.sleep(2)  # Respect rate limits

# Summary
print(f"\n{'='*60}")
print("📊 SUMMARY OF 3-TIER ATH RESULTS:")
print(f"{'='*60}")
for r in results:
    print(f"\n{r['ticker']} ({r['group']}):")
    print(f"  Peak: ${r['ath_high']:.12f} ({r['high_roi']:,.1f}%)")
    print(f"  Close: ${r['ath_close']:.12f} ({r['close_roi']:,.1f}%) ← More realistic")
    print(f"  Time: {r['ath_datetime']}")
