import os
from supabase import create_client
from dotenv import load_dotenv
import requests
import time

load_dotenv()
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

# Check the tokens mentioned in the conversation
tokens_to_check = ['FINESHYT', 'OZZY', 'BIP177', 'EASY', 'LOA', '3BAI']

print('=== CHECKING TOKENS FROM CONVERSATION ===')
print('These were mentioned as having wrong prices:\n')

for ticker in tokens_to_check:
    result = supabase.table('crypto_calls').select(
        'ticker, contract_address, network, current_price, price_at_call, roi_percent, price_updated_at'
    ).eq('ticker', ticker).limit(1).execute()
    
    if result.data:
        token = result.data[0]
        print(f'{ticker}:')
        
        if token['current_price']:
            print(f'  Current Price: ${token["current_price"]}')
            print(f'  Entry Price: ${token["price_at_call"] if token["price_at_call"] else "None"}')
            
            if token['roi_percent'] is not None:
                print(f'  ROI: {token["roi_percent"]:.1f}%')
            
            print(f'  Last Updated: {token["price_updated_at"][:19] if token["price_updated_at"] else "Never"}')
            
            # Check actual price if we have a contract
            if token['contract_address']:
                time.sleep(0.2)  # Rate limit
                response = requests.get(f'https://api.dexscreener.com/latest/dex/tokens/{token["contract_address"]}')
                if response.status_code == 200:
                    data = response.json()
                    if data.get('pairs') and len(data['pairs']) > 0:
                        actual = float(data['pairs'][0]['priceUsd'])
                        diff = abs(token['current_price'] - actual) / actual * 100
                        print(f'  API Price: ${actual}')
                        print(f'  Accuracy: {"✅ Correct" if diff < 10 else f"❌ {diff:.0f}% off"}')
                    else:
                        print(f'  Status: No pairs found (likely dead)')
                        
        else:
            print(f'  Current Price: None (reset as dead token)')
            print(f'  Entry Price: ${token["price_at_call"] if token["price_at_call"] else "None"}')
            
    print()