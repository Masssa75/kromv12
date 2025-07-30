import os
from supabase import create_client, Client
from dotenv import load_dotenv
import requests
import time

load_dotenv()

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

print("=== FIXING BATCH PROCESSOR PRICE ERRORS ===")
print("Finding and fixing tokens with unrealistic prices...\n")

# Get tokens with suspiciously high prices or ROI
# These are likely decimal point errors from the batch processor
suspicious_tokens = []

# Find tokens with ROI > 10,000%
high_roi = supabase.table('crypto_calls').select('krom_id, ticker, contract_address, network, price_at_call, current_price, roi_percent').gt('roi_percent', 10000).not_.is_('contract_address', 'null').execute()
suspicious_tokens.extend(high_roi.data)

# Find tokens with current price > $1000 (unlikely for most crypto)
high_price = supabase.table('crypto_calls').select('krom_id, ticker, contract_address, network, price_at_call, current_price, roi_percent').gt('current_price', 1000).not_.is_('contract_address', 'null').execute()
for token in high_price.data:
    if not any(t['krom_id'] == token['krom_id'] for t in suspicious_tokens):
        suspicious_tokens.append(token)

print(f"Found {len(suspicious_tokens)} suspicious tokens to check\n")

fixed_count = 0
errors = 0
network_map = {
    'ethereum': 'eth',
    'solana': 'solana',
    'bsc': 'bsc',
    'polygon': 'polygon',
    'arbitrum': 'arbitrum',
    'base': 'base'
}

for i, token in enumerate(suspicious_tokens):
    if i >= 50:  # Limit to first 50 to avoid rate limits
        print(f"\nStopping at 50 tokens. Run again to fix more.")
        break
        
    print(f"\n[{i+1}/{min(len(suspicious_tokens), 50)}] Checking {token['ticker']}...")
    print(f"  Current DB price: ${token['current_price']}")
    print(f"  Current ROI: {token['roi_percent']:.0f}%")
    
    # Get actual price
    actual_price = None
    
    # Try DexScreener first
    try:
        response = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{token['contract_address']}")
        if response.status_code == 200:
            data = response.json()
            if data.get('pairs') and len(data['pairs']) > 0:
                actual_price = float(data['pairs'][0]['priceUsd'])
                print(f"  DexScreener price: ${actual_price}")
    except Exception as e:
        print(f"  DexScreener error: {e}")
    
    # If not found, try GeckoTerminal
    if actual_price is None and token['network']:
        try:
            api_network = network_map.get(token['network'], token['network'])
            gecko_response = requests.get(f"https://api.geckoterminal.com/api/v2/networks/{api_network}/tokens/{token['contract_address']}/pools")
            
            if gecko_response.status_code == 200:
                gecko_data = gecko_response.json()
                if gecko_data.get('data') and len(gecko_data['data']) > 0:
                    pool_price = gecko_data['data'][0]['attributes'].get('token_price_usd')
                    if pool_price:
                        actual_price = float(pool_price)
                        print(f"  GeckoTerminal price: ${actual_price}")
        except Exception as e:
            print(f"  GeckoTerminal error: {e}")
    
    if actual_price and actual_price > 0:
        # Check if the price is drastically different
        price_ratio = token['current_price'] / actual_price
        
        if price_ratio > 100:  # Price is more than 100x too high
            print(f"  ❌ Price is {price_ratio:.0f}x too high!")
            
            # Calculate correct ROI
            if token['price_at_call'] and token['price_at_call'] > 0:
                correct_roi = ((actual_price - token['price_at_call']) / token['price_at_call']) * 100
            else:
                correct_roi = None
            
            # Update database
            update_data = {
                'current_price': actual_price,
                'price_updated_at': 'now()'
            }
            if correct_roi is not None:
                update_data['roi_percent'] = correct_roi
            
            update_result = supabase.table('crypto_calls').update(update_data).eq('krom_id', token['krom_id']).execute()
            
            print(f"  ✅ FIXED! New price: ${actual_price}")
            if correct_roi is not None:
                print(f"  ✅ New ROI: {correct_roi:.1f}%")
            fixed_count += 1
        else:
            print(f"  ✓ Price looks reasonable (ratio: {price_ratio:.1f}x)")
    else:
        print(f"  ⚠️  Could not fetch actual price")
        errors += 1
    
    time.sleep(0.3)  # Rate limit

print(f"\n=== SUMMARY ===")
print(f"Fixed {fixed_count} incorrect prices")
print(f"Couldn't verify {errors} tokens")
print(f"Tokens remaining to check: {max(0, len(suspicious_tokens) - 50)}")
