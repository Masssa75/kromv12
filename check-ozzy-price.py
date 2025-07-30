import os
from supabase import create_client, Client
from dotenv import load_dotenv
import requests

load_dotenv()

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

# Find OZZY token
ozzy = supabase.table('crypto_calls').select('*').eq('ticker', 'OZZY').execute()

print('=== OZZY TOKEN DATA ===')
for token in ozzy.data:
    print(f"KROM ID: {token['krom_id']}")
    print(f"Contract: {token['contract_address']}")
    print(f"Network: {token['network']}")
    print(f"Price at call: ${token['price_at_call']}")
    print(f"Current price: ${token['current_price']}")
    print(f"ROI: {token['roi_percent']:.1f}%" if token['roi_percent'] else "ROI: None")
    print(f"Price updated: {token['price_updated_at']}")
    print(f"Buy timestamp: {token['buy_timestamp']}")
    
    # Check actual current price from DexScreener
    if token['contract_address']:
        print("\n=== CHECKING ACTUAL CURRENT PRICE ===")
        
        # Try DexScreener
        response = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{token['contract_address']}")
        if response.status_code == 200:
            data = response.json()
            if data.get('pairs') and len(data['pairs']) > 0:
                actual_price = float(data['pairs'][0]['priceUsd'])
                print(f"DexScreener price: ${actual_price}")
                print(f"Database price: ${token['current_price']}")
                print(f"Price difference: {(token['current_price'] / actual_price - 1) * 100:.1f}% higher in DB")
                
                # Show correct ROI
                if token['price_at_call']:
                    correct_roi = ((actual_price - token['price_at_call']) / token['price_at_call']) * 100
                    print(f"\nCorrect ROI should be: {correct_roi:.1f}%")
                    print(f"Database ROI: {token['roi_percent']:.1f}%" if token['roi_percent'] else "None")
    print("\n" + "="*50 + "\n")
