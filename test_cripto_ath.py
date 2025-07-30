import requests
from datetime import datetime

# CRIPTO entries
cripto_calls = [
    {
        'id': '337b9af4-99cc-4798-b35c-9f0cbf3f884b',
        'pool': 'EGDkPgFFE1dBmpABoSjV4g3x5nKd2HiQytW5GP4v3BJ2',
        'call_time': '2025-05-19T03:09:00+00:00',
        'price_at_call': 0.0001515840
    },
    {
        'id': 'eddba872-ebc1-496d-8da4-f7a4b1a8b154',
        'pool': 'EGDkPgFFE1dBmpABoSjV4g3x5nKd2HiQytW5GP4v3BJ2',
        'call_time': '2025-05-19T03:10:00+00:00',
        'price_at_call': 0.0001819468
    }
]

for call in cripto_calls:
    call_dt = datetime.fromisoformat(call['call_time'].replace('+00:00', ''))
    call_timestamp_unix = int(call_dt.timestamp())
    
    print(f"\nCRIPTO Call #{cripto_calls.index(call) + 1}:")
    print(f"Call time: {call['call_time']}")
    print(f"Price at call: ${call['price_at_call']:.10f}")
    
    # Fetch OHLCV data
    url = f"https://api.geckoterminal.com/api/v2/networks/solana/pools/{call['pool']}/ohlcv/day"
    response = requests.get(url, params={'aggregate': 1, 'limit': 365})
    data = response.json()
    
    if 'data' in data and 'attributes' in data['data']:
        ohlcv_list = data['data']['attributes']['ohlcv_list']
        
        # Find ATH after call
        ath_price = 0
        ath_date = None
        
        for entry in ohlcv_list:
            if entry[0] >= call_timestamp_unix and entry[2]:
                high = float(entry[2])
                if high > ath_price:
                    ath_price = high
                    ath_date = datetime.fromtimestamp(entry[0]).strftime('%Y-%m-%d')
        
        if ath_price > 0:
            ath_roi = ((ath_price - call['price_at_call']) / call['price_at_call']) * 100
            print(f"ATH: ${ath_price:.10f} on {ath_date} (ROI: {ath_roi:+.2f}%)")
