import requests
from datetime import datetime

# TCM data
pool_address = "FPDxQgk3vDJnQM1HH2D5SuLsmCDNTBRgSU5PZA5EkZDr"
call_timestamp_str = "2025-05-18T15:11:00+00:00"
price_at_call = 0.0000951165

# Convert to unix timestamp
call_dt = datetime.fromisoformat(call_timestamp_str.replace('+00:00', ''))
call_timestamp_unix = int(call_dt.timestamp())

print(f"Call date: {call_timestamp_str}")
print(f"Call timestamp: {call_timestamp_unix}")
print(f"Price at call: ${price_at_call:.10f}")

# Fetch OHLCV data
url = f"https://api.geckoterminal.com/api/v2/networks/solana/pools/{pool_address}/ohlcv/day"
response = requests.get(url, params={'aggregate': 1, 'limit': 365})
data = response.json()

ohlcv_list = data['data']['attributes']['ohlcv_list']

# Find entries after call
entries_after_call = []
for entry in ohlcv_list:
    if entry[0] >= call_timestamp_unix:
        entries_after_call.append({
            'timestamp': entry[0],
            'date': datetime.fromtimestamp(entry[0]).strftime('%Y-%m-%d'),
            'high': float(entry[2]) if entry[2] else 0
        })

# Sort by high price
entries_after_call.sort(key=lambda x: x['high'], reverse=True)

print(f"\nTop 5 highest prices after call:")
for i, entry in enumerate(entries_after_call[:5]):
    roi = ((entry['high'] - price_at_call) / price_at_call) * 100
    print(f"{i+1}. {entry['date']}: ${entry['high']:.10f} (ROI: {roi:+.2f}%)")

# Get ATH
if entries_after_call:
    ath = entries_after_call[0]
    ath_roi = ((ath['high'] - price_at_call) / price_at_call) * 100
    print(f"\nATH Summary:")
    print(f"  Price: ${ath['high']:.10f}")
    print(f"  Date: {ath['date']}")
    print(f"  ROI: {ath_roi:+.2f}%")
