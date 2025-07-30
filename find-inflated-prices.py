import os
from supabase import create_client
from dotenv import load_dotenv
import requests

load_dotenv()
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

# Get tokens with very high ROI (likely wrong prices)
result = supabase.table('crypto_calls').select(
    'ticker, contract_address, network, current_price, price_at_call, roi_percent, price_updated_at'
).not_.is_('current_price', 'null').gt('roi_percent', 1000).order('roi_percent', desc=True).limit(10).execute()

print('Tokens with inflated prices (ROI > 1000%):')
for token in result.data:
    print(f"\n{token['ticker']}:")
    print(f"  Contract: {token['contract_address']}")
    print(f"  Network: {token['network']}")
    print(f"  Entry Price: ${token['price_at_call']}")
    print(f"  Current Price: ${token['current_price']}")
    print(f"  ROI: {token['roi_percent']:.0f}%")
    print(f"  Last Updated: {token['price_updated_at']}")
    
    # Test actual price with DexScreener
    if token['contract_address']:
        response = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{token['contract_address']}")
        if response.status_code == 200:
            data = response.json()
            if data.get('pairs') and len(data['pairs']) > 0:
                actual_price = float(data['pairs'][0]['priceUsd'])
                print(f"  ✅ DexScreener Price: ${actual_price}")
                print(f"  📊 DB vs Actual: {abs(token['current_price'] - actual_price) / actual_price * 100:.0f}% off")