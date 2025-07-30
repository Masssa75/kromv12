import os
from supabase import create_client, Client
from dotenv import load_dotenv
import requests
import time

load_dotenv()

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

print("=== CHECKING FOR PRICE ANOMALIES ===")
print("Looking for tokens where current price seems wrong...\n")

# Get tokens with large positive ROI (>100%) as these might be errors
suspicious = supabase.table('crypto_calls').select('krom_id, ticker, contract_address, network, price_at_call, current_price, roi_percent, price_updated_at').gt('roi_percent', 100).order('roi_percent', desc=True).limit(20).execute()

print(f"Found {len(suspicious.data)} tokens with >100% ROI (checking if legitimate)\n")

fixed_count = 0
errors = 0

for token in suspicious.data:
    if not token['contract_address']:
        continue
        
    print(f"Checking {token['ticker']} (ROI: {token['roi_percent']:.1f}%)...")
    
    # Check actual price
    try:
        response = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{token['contract_address']}")
        if response.status_code == 200:
            data = response.json()
            if data.get('pairs') and len(data['pairs']) > 0:
                actual_price = float(data['pairs'][0]['priceUsd'])
                db_price = token['current_price']
                
                # Calculate price difference
                if actual_price > 0:
                    price_ratio = db_price / actual_price
                    
                    # If database price is more than 5x different, it's likely wrong
                    if price_ratio > 5 or price_ratio < 0.2:
                        print(f"  ❌ WRONG PRICE FOUND!")
                        print(f"     DB price: ${db_price}")
                        print(f"     Actual: ${actual_price}")
                        print(f"     Ratio: {price_ratio:.1f}x")
                        
                        # Calculate correct ROI
                        correct_roi = ((actual_price - token['price_at_call']) / token['price_at_call']) * 100
                        
                        # Update database
                        update_result = supabase.table('crypto_calls').update({
                            'current_price': actual_price,
                            'roi_percent': correct_roi,
                            'price_updated_at': 'now()'
                        }).eq('krom_id', token['krom_id']).execute()
                        
                        print(f"     ✅ Fixed! New ROI: {correct_roi:.1f}%\n")
                        fixed_count += 1
                    else:
                        print(f"  ✓ Price looks correct (ratio: {price_ratio:.1f}x)\n")
                        
        time.sleep(0.5)  # Rate limit
        
    except Exception as e:
        print(f"  Error: {e}\n")
        errors += 1

print(f"\n=== SUMMARY ===")
print(f"Fixed {fixed_count} incorrect prices")
print(f"Errors: {errors}")

# Also check tokens with very negative ROI that might be inverted
print("\n=== CHECKING VERY NEGATIVE ROI (<-99%) ===")
very_negative = supabase.table('crypto_calls').select('krom_id, ticker, contract_address, network, price_at_call, current_price, roi_percent').lt('roi_percent', -99).limit(10).execute()

for token in very_negative.data[:5]:  # Just check first 5
    print(f"{token['ticker']}: {token['roi_percent']:.1f}% ROI")
    print(f"  Entry: ${token['price_at_call']}")
    print(f"  Current: ${token['current_price']}")
