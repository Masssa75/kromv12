import requests
from datetime import datetime

# Get the earliest BOOCHIE Ethereum data
call_data = {
    "id": "71881f90-b996-4f20-8ca4-97100de1156d",
    "ticker": "BOOCHIE",
    "contract_address": "0xF8EA18Ca502De3FFAA9B8Ed95a21878eE41A2f4A",
    "network": "ethereum",
    "price_at_call": 8E-10,
    "current_price": 5.24E-10,
    "pool_address": "0x9392a42AbE7E8131E0956De4F8A0413f2a0e52BF",
    "group": "TopCallersChannel",
    "timestamp": 1747688939
}

# Convert timestamp to readable date
call_date = datetime.fromtimestamp(call_data['timestamp']).strftime('%Y-%m-%d %H:%M:%S UTC')

print(f"=== {call_data['ticker']} ATH Analysis ===")
print(f"Group: {call_data['group']}")
print(f"Network: {call_data['network'].upper()}")
print(f"Call date: {call_date}")
print(f"Price at call: ${call_data['price_at_call']:.12f}")
print(f"Current price: ${call_data['current_price']:.12f}")
print(f"Contract: {call_data['contract_address']}")

# Fetch OHLCV data
url = f"https://api.geckoterminal.com/api/v2/networks/eth/pools/{call_data['pool_address']}/ohlcv/day"
response = requests.get(url, params={'aggregate': 1, 'limit': 365})
data = response.json()

if 'data' in data and 'attributes' in data['data']:
    ohlcv_list = data['data']['attributes']['ohlcv_list']
    
    # Find all prices after call
    prices_after_call = []
    
    for entry in ohlcv_list:
        if entry[0] >= call_data['timestamp'] and entry[2]:
            prices_after_call.append({
                'timestamp': entry[0],
                'date': datetime.fromtimestamp(entry[0]).strftime('%Y-%m-%d'),
                'high': float(entry[2])
            })
    
    # Sort by high price
    prices_after_call.sort(key=lambda x: x['high'], reverse=True)
    
    if prices_after_call:
        # ATH summary
        ath = prices_after_call[0]
        ath_roi = ((ath['high'] - call_data['price_at_call']) / call_data['price_at_call']) * 100
        
        print(f"\n📈 ATH SUMMARY:")
        print(f"  Price: ${ath['high']:.12f}")
        print(f"  Date: {ath['date']}")
        print(f"  ROI: {ath_roi:+.2f}%")
        print(f"  Multiplier: {ath_roi/100 + 1:.1f}x")
        
        # Current ROI
        current_roi = ((call_data['current_price'] - call_data['price_at_call']) / call_data['price_at_call']) * 100
        print(f"\n📊 CURRENT STATUS:")
        print(f"  Current ROI: {current_roi:+.2f}%")
        print(f"  Days tracked: {len(prices_after_call)}")
        
        # Show top 3 prices
        print(f"\n🔝 Top 3 prices after call:")
        for i, price_data in enumerate(prices_after_call[:3]):
            roi = ((price_data['high'] - call_data['price_at_call']) / call_data['price_at_call']) * 100
            print(f"  {i+1}. {price_data['date']}: ${price_data['high']:.12f} (ROI: {roi:+.2f}%)")
