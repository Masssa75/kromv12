import os
from supabase import create_client, Client
from dotenv import load_dotenv
import requests
import time

load_dotenv()

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

# Find FINESHYT
print('=== CHECKING FINESHYT ===')
fineshyt = supabase.table('crypto_calls').select('*').eq('ticker', 'FINESHYT').execute()

for token in fineshyt.data:
    print(f"\nKROM ID: {token['krom_id']}")
    print(f"Contract: {token['contract_address']}")
    print(f"Network: {token['network']}")
    print(f"Price at call: ${token['price_at_call']}")
    print(f"Current price (DB): ${token['current_price']}")
    print(f"ROI: {token['roi_percent']:.1f}%" if token['roi_percent'] else 'None')
    print(f"Last updated: {token['price_updated_at']}")
    
    # Check actual price
    if token['contract_address']:
        print("\nChecking actual price...")
        
        # Try DexScreener first
        response = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{token['contract_address']}")
        if response.status_code == 200:
            data = response.json()
            if data.get('pairs') and len(data['pairs']) > 0:
                actual_price = float(data['pairs'][0]['priceUsd'])
                print(f"DexScreener price: ${actual_price}")
                print(f"DB vs Actual difference: {abs(token['current_price'] - actual_price) / actual_price * 100:.1f}%")
                
                # Calculate correct ROI
                if token['price_at_call'] and token['price_at_call'] > 0:
                    correct_roi = ((actual_price - token['price_at_call']) / token['price_at_call']) * 100
                    print(f"\nCorrect ROI should be: {correct_roi:.1f}%")
                    print(f"DB shows ROI: {token['roi_percent']:.1f}%" if token['roi_percent'] else 'None')
            else:
                print("No pairs found on DexScreener")
                
                # Try GeckoTerminal
                print("\nTrying GeckoTerminal...")
                time.sleep(0.5)
                gecko_response = requests.get(f"https://api.geckoterminal.com/api/v2/networks/solana/tokens/{token['contract_address']}/pools")
                if gecko_response.status_code == 200:
                    gecko_data = gecko_response.json()
                    if gecko_data.get('data') and len(gecko_data['data']) > 0:
                        pool_price = gecko_data['data'][0]['attributes'].get('token_price_usd')
                        if pool_price:
                            actual_price = float(pool_price)
                            print(f"GeckoTerminal price: ${actual_price}")
                            print(f"DB vs Actual difference: {abs(token['current_price'] - actual_price) / actual_price * 100:.1f}%")
                            
                            if token['price_at_call'] and token['price_at_call'] > 0:
                                correct_roi = ((actual_price - token['price_at_call']) / token['price_at_call']) * 100
                                print(f"\nCorrect ROI should be: {correct_roi:.1f}%")
                                print(f"DB shows ROI: {token['roi_percent']:.1f}%")

# Also check BIP177 for comparison
print("\n\n=== CHECKING BIP177 (for comparison) ===")
bip177 = supabase.table('crypto_calls').select('*').eq('ticker', 'BIP177').limit(1).execute()

for token in bip177.data:
    print(f"\nContract: {token['contract_address']}")
    print(f"Current price (DB): ${token['current_price']}")
    print(f"ROI: {token['roi_percent']:.1f}%" if token['roi_percent'] else 'None')
    
    if token['contract_address']:
        response = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{token['contract_address']}")
        if response.status_code == 200:
            data = response.json()
            if data.get('pairs') and len(data['pairs']) > 0:
                actual_price = float(data['pairs'][0]['priceUsd'])
                print(f"DexScreener price: ${actual_price}")
                print(f"Price match: {'YES' if abs(token['current_price'] - actual_price) / actual_price * 100 < 5 else 'NO'}")