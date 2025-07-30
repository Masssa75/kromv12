import os
from supabase import create_client
from dotenv import load_dotenv
import requests
import time

load_dotenv()
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

# Get tokens with extremely high ROI (likely wrong prices)
result = supabase.table('crypto_calls').select(
    'id, krom_id, ticker, contract_address, network, current_price, price_at_call, roi_percent'
).not_.is_('current_price', 'null').gt('roi_percent', 10000).order('roi_percent', desc=True).limit(20).execute()

print(f'Found {len(result.data)} tokens with ROI > 10,000% (likely wrong prices)\n')

fixed_count = 0
failed_count = 0

for token in result.data:
    print(f"\nFixing {token['ticker']} (ROI: {token['roi_percent']:.0f}%)...")
    print(f"  Current wrong price: ${token['current_price']}")
    
    # Try DexScreener first
    if token['contract_address']:
        response = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{token['contract_address']}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('pairs') and len(data['pairs']) > 0:
                # Get the first pair (usually highest liquidity)
                correct_price = float(data['pairs'][0]['priceUsd'])
                
                # Calculate correct ROI
                if token['price_at_call'] and token['price_at_call'] > 0:
                    correct_roi = ((correct_price - token['price_at_call']) / token['price_at_call']) * 100
                else:
                    correct_roi = None
                
                print(f"  ✅ Found correct price: ${correct_price}")
                print(f"  Correct ROI: {correct_roi:.1f}%" if correct_roi else "  No entry price for ROI")
                
                # Update database
                update_data = {
                    'current_price': correct_price,
                    'price_updated_at': 'now()'
                }
                if correct_roi is not None:
                    update_data['roi_percent'] = correct_roi
                
                update_result = supabase.table('crypto_calls').update(update_data).eq('krom_id', token['krom_id']).execute()
                
                if update_result.data:
                    print(f"  ✅ Updated successfully!")
                    fixed_count += 1
                else:
                    print(f"  ❌ Failed to update database")
                    failed_count += 1
            else:
                print(f"  ⚠️ No pairs found on DexScreener")
                
                # Try manual price reset for dead tokens
                if token['roi_percent'] > 1000000:  # Over 1M% ROI is definitely wrong
                    print(f"  🔧 Resetting to null (token likely dead)")
                    update_result = supabase.table('crypto_calls').update({
                        'current_price': None,
                        'roi_percent': None,
                        'price_updated_at': 'now()'
                    }).eq('krom_id', token['krom_id']).execute()
                    
                    if update_result.data:
                        print(f"  ✅ Reset to null")
                        fixed_count += 1
        else:
            print(f"  ❌ DexScreener API error: {response.status_code}")
            failed_count += 1
    
    # Rate limit
    time.sleep(0.3)

print(f"\n\n=== SUMMARY ===")
print(f"Fixed: {fixed_count} tokens")
print(f"Failed: {failed_count} tokens")
print(f"Total processed: {len(result.data)} tokens")