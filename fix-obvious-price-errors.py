import os
from supabase import create_client, Client
from dotenv import load_dotenv
import requests
import time

load_dotenv()

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

print("=== FIXING OBVIOUSLY WRONG PRICES ===")
print("Targeting tokens where current_price doesn't match ROI calculation\n")

# Get tokens where the price and ROI don't match
# This query finds tokens where the calculated ROI differs significantly from stored ROI
all_tokens = supabase.table('crypto_calls').select(
    'krom_id, ticker, contract_address, network, price_at_call, current_price, roi_percent'
).not_.is_('price_at_call', 'null').not_.is_('current_price', 'null').not_.is_('roi_percent', 'null').not_.is_('contract_address', 'null').execute()

print(f"Checking {len(all_tokens.data)} tokens for price/ROI mismatches...\n")

mismatched = []
for token in all_tokens.data:
    if token['price_at_call'] > 0:
        # Calculate what ROI should be based on prices
        calculated_roi = ((token['current_price'] - token['price_at_call']) / token['price_at_call']) * 100
        
        # Check if ROI matches (within 1% tolerance for rounding)
        roi_diff = abs(calculated_roi - token['roi_percent'])
        
        if roi_diff > 1:  # More than 1% difference
            mismatched.append({
                **token,
                'calculated_roi': calculated_roi,
                'roi_diff': roi_diff
            })

print(f"Found {len(mismatched)} tokens with mismatched price/ROI\n")

# Sort by ROI difference to fix worst ones first
mismatched.sort(key=lambda x: x['roi_diff'], reverse=True)

fixed_count = 0
network_map = {
    'ethereum': 'eth',
    'solana': 'solana',
    'bsc': 'bsc',
    'polygon': 'polygon',
    'arbitrum': 'arbitrum',
    'base': 'base'
}

# Fix top 50 worst mismatches
for i, token in enumerate(mismatched[:50]):
    print(f"\n[{i+1}/50] {token['ticker']}:")
    print(f"  Price: ${token['current_price']} | Stored ROI: {token['roi_percent']:.1f}%")
    print(f"  Calculated ROI from prices: {token['calculated_roi']:.1f}%")
    print(f"  Difference: {token['roi_diff']:.0f}% - MAJOR MISMATCH!")
    
    # Get actual price
    actual_price = None
    
    # Try DexScreener
    try:
        response = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{token['contract_address']}")
        if response.status_code == 200:
            data = response.json()
            if data.get('pairs') and len(data['pairs']) > 0:
                actual_price = float(data['pairs'][0]['priceUsd'])
                print(f"  DexScreener price: ${actual_price}")
    except:
        pass
    
    # Try GeckoTerminal if needed
    if actual_price is None and token['network']:
        try:
            api_network = network_map.get(token['network'], token['network'])
            response = requests.get(f"https://api.geckoterminal.com/api/v2/networks/{api_network}/tokens/{token['contract_address']}/pools")
            if response.status_code == 200:
                data = response.json()
                if data.get('data') and len(data['data']) > 0:
                    pool_price = data['data'][0]['attributes'].get('token_price_usd')
                    if pool_price:
                        actual_price = float(pool_price)
                        print(f"  GeckoTerminal price: ${actual_price}")
            time.sleep(0.2)
        except:
            pass
    
    if actual_price and actual_price > 0:
        # Calculate correct ROI
        correct_roi = ((actual_price - token['price_at_call']) / token['price_at_call']) * 100
        
        # Update database
        update_result = supabase.table('crypto_calls').update({
            'current_price': actual_price,
            'roi_percent': correct_roi,
            'price_updated_at': 'now()'
        }).eq('krom_id', token['krom_id']).execute()
        
        print(f"  ✅ FIXED! New price: ${actual_price}, New ROI: {correct_roi:.1f}%")
        fixed_count += 1
    else:
        print(f"  ⚠️  Could not fetch actual price")
    
    time.sleep(0.3)

print(f"\n=== SUMMARY ===")
print(f"Fixed {fixed_count} tokens with mismatched price/ROI")
print(f"Remaining mismatched tokens: {len(mismatched) - 50}")
