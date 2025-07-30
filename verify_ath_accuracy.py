import requests
from datetime import datetime, timedelta
import time
import sys

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

def find_ath_3tier(network, pool_address, call_timestamp, ticker):
    """3-tier approach: daily -> hourly -> minute"""
    
    # TIER 1: Daily candles
    daily_candles = get_ohlcv_data(network, pool_address, 'day', limit=1000)
    
    if not daily_candles:
        return None
    
    # Find highest daily candle after call
    daily_highs = []
    for candle in daily_candles:
        if candle[0] >= call_timestamp and candle[2]:
            daily_highs.append({
                'timestamp': candle[0],
                'high': float(candle[2])
            })
    
    if not daily_highs:
        return None
    
    daily_highs.sort(key=lambda x: x['high'], reverse=True)
    daily_ath = daily_highs[0]
    
    # TIER 2: Hourly candles around ATH day
    before_ts = daily_ath['timestamp'] + (3 * 24 * 3600)  # 3 days after
    hourly_candles = get_ohlcv_data(network, pool_address, 'hour', limit=168, before_timestamp=before_ts)
    
    hourly_highs = []
    for candle in hourly_candles:
        # Only look at candles around the ATH day (±1 day)
        if abs(candle[0] - daily_ath['timestamp']) <= 86400 and candle[2]:
            hourly_highs.append({
                'timestamp': candle[0],
                'high': float(candle[2])
            })
    
    if not hourly_highs:
        return None
        
    hourly_highs.sort(key=lambda x: x['high'], reverse=True)
    hourly_ath = hourly_highs[0]
    
    # TIER 3: Minute candles around ATH hour
    before_ts = hourly_ath['timestamp'] + (2 * 3600)  # 2 hours after
    minute_candles = get_ohlcv_data(network, pool_address, 'minute', limit=240, before_timestamp=before_ts)
    
    minute_data = []
    for candle in minute_candles:
        # Only look at candles around the ATH hour (±1 hour)
        if abs(candle[0] - hourly_ath['timestamp']) <= 3600 and candle[1] and candle[2] and candle[4]:
            minute_data.append({
                'timestamp': candle[0],
                'open': float(candle[1]),
                'high': float(candle[2]),
                'close': float(candle[4])
            })
    
    if not minute_data:
        return None
        
    # Find the minute with highest high
    minute_data.sort(key=lambda x: x['high'], reverse=True)
    minute_ath = minute_data[0]
    
    # ATH price is max(open, close) from that minute
    ath_price = max(minute_ath['open'], minute_ath['close'])
    
    return {
        'ath_price': ath_price,
        'ath_timestamp': minute_ath['timestamp'],
        'ath_datetime': datetime.fromtimestamp(minute_ath['timestamp']).strftime('%Y-%m-%d %H:%M')
    }

# Verification test cases from database
test_tokens = [
    {
        'ticker': 'DVERIFY',
        'network': 'eth',  # ethereum -> eth for GeckoTerminal
        'pool_address': '0x0b92563603b94C76fce478AD1579AC57B9F96972',
        'price_at_call': 0.0798859375,
        'db_ath_price': 0.268265124802919,
        'db_ath_timestamp': '2025-07-28 14:58:00+00',
        'db_ath_roi_percent': 235.8101978873553,
        'buy_timestamp': 1747904044  # 2025-05-20 10:14:04 UTC
    },
    {
        'ticker': 'FLUX',
        'network': 'solana',
        'pool_address': '8CSMLqmt4ZJMxaK2K7qtWEXaAHUMyNDr4dQpfhpsC3pT',
        'price_at_call': 0.0000468087,
        'db_ath_price': 0.0002977823067242811,
        'db_ath_timestamp': '2025-07-27 15:17:00+00',
        'db_ath_roi_percent': 536.1687180466048,
        'buy_timestamp': 1747925645  # 2025-05-20 16:14:05 UTC
    },
    {
        'ticker': 'KOLT',
        'network': 'eth',  # ethereum -> eth
        'pool_address': '0xd792905861d6F973C6CD5Ce539347409e040966C',
        'price_at_call': 0.0535572605,
        'db_ath_price': 0.240133263705166,
        'db_ath_timestamp': '2025-07-22 02:45:00+00',
        'db_ath_roi_percent': 348.367338925347,
        'buy_timestamp': 1747913224  # 2025-05-20 13:07:04 UTC
    },
    {
        'ticker': 'YLT',
        'network': 'solana',
        'pool_address': 'EckoPfSc4XcBockkqJ5XkbBdgoa6hUnCauhu7J3baWsR',
        'price_at_call': 0.0092186218,
        'db_ath_price': 0.011273635993635516,
        'db_ath_timestamp': '2025-07-12 21:36:00+00',
        'db_ath_roi_percent': 22.29198939081671,
        'buy_timestamp': 1747736408  # 2025-05-19 09:30:08 UTC
    },
    {
        'ticker': 'CMD',
        'network': 'solana',
        'pool_address': '8kaEhweQhLXQ2bbCaUbcmAW54ozwgTR1SxCrVWqSFjB9',
        'price_at_call': 0.0048418463,
        'db_ath_price': 0.015497491201666077,
        'db_ath_timestamp': '2025-07-02 19:04:00+00',
        'db_ath_roi_percent': 220.07400155734143,
        'buy_timestamp': 1747722184  # 2025-05-19 07:43:04 UTC
    }
]

# Run verification with delay to respect rate limits
print("=" * 80)
print("ATH CALCULATION VERIFICATION REPORT")
print("=" * 80)
print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Verifying {len(test_tokens)} tokens with manual 3-tier ATH calculation")
print("=" * 80)

results = []
for i, token in enumerate(test_tokens):
    print(f"\n[{i+1}/{len(test_tokens)}] Verifying {token['ticker']} on {token['network'].upper()}...")
    
    # Perform manual calculation
    manual_result = find_ath_3tier(
        token['network'], 
        token['pool_address'],
        token['buy_timestamp'],
        token['ticker']
    )
    
    if manual_result:
        # Calculate manual ROI
        manual_roi = max(0, ((manual_result['ath_price'] - token['price_at_call']) / token['price_at_call']) * 100)
        
        # Compare with database values
        price_diff_pct = abs(manual_result['ath_price'] - token['db_ath_price']) / token['db_ath_price'] * 100
        roi_diff = abs(manual_roi - token['db_ath_roi_percent'])
        
        # Parse database timestamp
        db_timestamp = datetime.strptime(token['db_ath_timestamp'].replace('+00', ''), '%Y-%m-%d %H:%M:%S')
        manual_timestamp = datetime.fromtimestamp(manual_result['ath_timestamp'])
        time_diff_hours = abs((db_timestamp - manual_timestamp).total_seconds() / 3600)
        
        status = "✅ PASS" if price_diff_pct < 1 and roi_diff < 1 else "❌ FAIL"
        
        result = {
            'ticker': token['ticker'],
            'network': token['network'],
            'status': status,
            'db_ath_price': token['db_ath_price'],
            'manual_ath_price': manual_result['ath_price'],
            'price_diff_pct': price_diff_pct,
            'db_roi': token['db_ath_roi_percent'],
            'manual_roi': manual_roi,
            'roi_diff': roi_diff,
            'db_timestamp': token['db_ath_timestamp'],
            'manual_timestamp': manual_result['ath_datetime'],
            'time_diff_hours': time_diff_hours
        }
        
        results.append(result)
        
        print(f"  Database ATH: ${token['db_ath_price']:.12f} (ROI: {token['db_ath_roi_percent']:.2f}%)")
        print(f"  Manual ATH:   ${manual_result['ath_price']:.12f} (ROI: {manual_roi:.2f}%)")
        print(f"  Price Diff:   {price_diff_pct:.2f}%")
        print(f"  ROI Diff:     {roi_diff:.2f}%")
        print(f"  Status:       {status}")
    else:
        results.append({
            'ticker': token['ticker'],
            'network': token['network'],
            'status': '⚠️  NO DATA',
            'db_ath_price': token['db_ath_price'],
            'manual_ath_price': None,
            'price_diff_pct': None,
            'db_roi': token['db_ath_roi_percent'],
            'manual_roi': None,
            'roi_diff': None
        })
        print(f"  Status:       ⚠️  NO DATA - Could not fetch OHLCV data")
    
    # Respect rate limits
    if i < len(test_tokens) - 1:
        time.sleep(6)

# Summary Report
print("\n" + "=" * 80)
print("VERIFICATION SUMMARY")
print("=" * 80)

passed = sum(1 for r in results if r['status'] == "✅ PASS")
failed = sum(1 for r in results if r['status'] == "❌ FAIL")
no_data = sum(1 for r in results if r['status'] == "⚠️  NO DATA")

print(f"Total Tokens Verified: {len(results)}")
print(f"✅ Passed: {passed}")
print(f"❌ Failed: {failed}")
print(f"⚠️  No Data: {no_data}")

if failed > 0:
    print("\n❌ FAILED TOKENS:")
    for r in results:
        if r['status'] == "❌ FAIL":
            print(f"\n  {r['ticker']} ({r['network']}):")
            print(f"    DB ATH:     ${r['db_ath_price']:.12f}")
            if r['manual_ath_price']:
                print(f"    Manual ATH: ${r['manual_ath_price']:.12f}")
                print(f"    Price Diff: {r['price_diff_pct']:.2f}%")
                print(f"    ROI Diff:   {r['roi_diff']:.2f}%")
            else:
                print(f"    Manual ATH: N/A")
                print(f"    Price Diff: N/A")
                print(f"    ROI Diff:   N/A")

print("\n" + "=" * 80)
print("DETAILED RESULTS")
print("=" * 80)

for r in results:
    print(f"\n{r['ticker']} ({r['network'].upper()}):")
    print(f"  Status: {r['status']}")
    if r['manual_ath_price'] is not None:
        print(f"  Database ATH vs Manual ATH:")
        print(f"    Price: ${r['db_ath_price']:.12f} vs ${r['manual_ath_price']:.12f} ({r['price_diff_pct']:.2f}% diff)")
        print(f"    ROI:   {r['db_roi']:.2f}% vs {r['manual_roi']:.2f}% ({r['roi_diff']:.2f}% diff)")
        print(f"    Time:  {r['db_timestamp']} vs {r['manual_timestamp']} ({r['time_diff_hours']:.1f}h diff)")