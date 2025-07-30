import os
from supabase import create_client, Client
from dotenv import load_dotenv
import requests
import random

load_dotenv()

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

print("=== TESTING PRICE ACCURACY ===")
print("Comparing database prices with actual API prices\n")

# Get a random sample of tokens with current prices
tokens = supabase.table('crypto_calls').select('ticker, contract_address, network, current_price, price_at_call, roi_percent').not_.is_('current_price', 'null').not_.is_('contract_address', 'null').limit(20).execute()

print(f"Checking {len(tokens.data)} random tokens...\n")

correct_count = 0
wrong_count = 0
total_checked = 0

for token in tokens.data:
    print(f"{token['ticker']}:")
    print(f"  Contract: {token['contract_address'][:10]}...")
    print(f"  DB Price: ${token['current_price']}")
    
    # Check actual price from DexScreener
    try:
        response = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{token['contract_address']}")
        if response.status_code == 200:
            data = response.json()
            if data.get('pairs') and len(data['pairs']) > 0:
                actual_price = float(data['pairs'][0]['priceUsd'])
                print(f"  API Price: ${actual_price}")
                
                # Calculate difference
                if actual_price > 0:
                    diff_percent = abs((token['current_price'] - actual_price) / actual_price * 100)
                    print(f"  Difference: {diff_percent:.1f}%")
                    
                    total_checked += 1
                    if diff_percent < 10:  # Within 10% is considered correct
                        print(f"  ✅ CORRECT\n")
                        correct_count += 1
                    else:
                        print(f"  ❌ WRONG (off by {diff_percent:.0f}%)\n")
                        wrong_count += 1
                else:
                    print(f"  ⚠️  API returned 0 price\n")
            else:
                print(f"  ⚠️  No pairs found on DexScreener\n")
        else:
            print(f"  ⚠️  API error: {response.status_code}\n")
    except Exception as e:
        print(f"  ⚠️  Error: {e}\n")

print("\n=== SUMMARY ===")
print(f"Total checked: {total_checked}")
print(f"Correct prices: {correct_count} ({correct_count/total_checked*100:.1f}%)" if total_checked > 0 else "No prices checked")
print(f"Wrong prices: {wrong_count} ({wrong_count/total_checked*100:.1f}%)" if total_checked > 0 else "")

# Check the refresh-prices endpoint logic
print("\n=== ANALYZING PRICE REFRESH LOGIC ===")
print("Looking at recently updated prices...\n")

# Get tokens updated in last hour
from datetime import datetime, timedelta
one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()

recent = supabase.table('crypto_calls').select('ticker, contract_address, current_price, price_updated_at').not_.is_('current_price', 'null').gte('price_updated_at', one_hour_ago).limit(10).execute()

print(f"Found {len(recent.data)} tokens updated in last hour")
for token in recent.data[:5]:
    print(f"\n{token['ticker']}: ${token['current_price']}")
    print(f"  Updated: {token['price_updated_at']}")
