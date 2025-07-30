import os
from supabase import create_client, Client
from dotenv import load_dotenv
import requests
import random

load_dotenv()

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

print("=== CHECKING TOKENS WITH MODERATE ROI ===")
print("Testing accuracy of tokens with 100-500% ROI...\n")

# Get tokens with moderate positive ROI
moderate_roi = supabase.table('crypto_calls').select('krom_id, ticker, contract_address, network, price_at_call, current_price, roi_percent, price_updated_at').not_.is_('contract_address', 'null').gte('roi_percent', 100).lte('roi_percent', 500).limit(20).execute()

print(f"Checking {len(moderate_roi.data)} tokens with 100-500% ROI\n")

correct = 0
wrong = 0

for token in moderate_roi.data[:10]:  # Check first 10
    print(f"\n{token['ticker']} (ROI: {token['roi_percent']:.1f}%):")
    print(f"  Entry: ${token['price_at_call']}")
    print(f"  DB Current: ${token['current_price']}")
    
    # Get actual price
    try:
        response = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{token['contract_address']}")
        if response.status_code == 200:
            data = response.json()
            if data.get('pairs') and len(data['pairs']) > 0:
                actual_price = float(data['pairs'][0]['priceUsd'])
                print(f"  API Price: ${actual_price}")
                
                # Calculate price difference
                diff_percent = abs((token['current_price'] - actual_price) / actual_price * 100)
                
                if diff_percent < 10:
                    print(f"  ✅ CORRECT (diff: {diff_percent:.1f}%)")
                    correct += 1
                else:
                    print(f"  ❌ WRONG (diff: {diff_percent:.0f}%)")
                    wrong += 1
                    
                    # Show what ROI should be
                    correct_roi = ((actual_price - token['price_at_call']) / token['price_at_call']) * 100
                    print(f"  Correct ROI should be: {correct_roi:.1f}%")
            else:
                print(f"  ⚠️  No data on DexScreener")
        else:
            print(f"  ⚠️  API error")
    except Exception as e:
        print(f"  ⚠️  Error: {e}")

print(f"\n\n=== CHECKING NEGATIVE ROI TOKENS ===")
print("Testing accuracy of tokens with -80% to -50% ROI...\n")

# Get tokens with moderate negative ROI  
negative_roi = supabase.table('crypto_calls').select('krom_id, ticker, contract_address, network, price_at_call, current_price, roi_percent').not_.is_('contract_address', 'null').gte('roi_percent', -80).lte('roi_percent', -50).limit(10).execute()

for token in negative_roi.data[:5]:
    print(f"\n{token['ticker']} (ROI: {token['roi_percent']:.1f}%):")
    print(f"  Entry: ${token['price_at_call']}")
    print(f"  DB Current: ${token['current_price']}")
    
    # Calculate what the price should be based on ROI
    expected_price = token['price_at_call'] * (1 + token['roi_percent']/100)
    print(f"  Expected based on ROI: ${expected_price}")
    
    price_matches = abs(token['current_price'] - expected_price) < 0.000001
    print(f"  Price matches ROI: {'YES' if price_matches else 'NO'}")

print(f"\n\n=== SUMMARY ===")
print(f"Moderate ROI tokens checked: {correct + wrong}")
print(f"Correct prices: {correct}")
print(f"Wrong prices: {wrong}")
