import os
from supabase import create_client, Client
from dotenv import load_dotenv
import requests
import time

load_dotenv()

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

# First, fix OZZY specifically
print("=== FIXING OZZY ===")
ozzy_contract = "9rB2Dmbdn4KpepcVgNCCmgS7yKgYA2RQx5auoWkhbonk"

# Get actual price
response = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{ozzy_contract}")
if response.status_code == 200:
    data = response.json()
    if data.get('pairs') and len(data['pairs']) > 0:
        actual_price = float(data['pairs'][0]['priceUsd'])
        print(f"Actual OZZY price: ${actual_price}")
        
        # Get OZZY data
        ozzy = supabase.table('crypto_calls').select('*').eq('contract_address', ozzy_contract).execute()
        
        for token in ozzy.data:
            if token['price_at_call']:
                correct_roi = ((actual_price - token['price_at_call']) / token['price_at_call']) * 100
                
                print(f"Updating OZZY (KROM ID: {token['krom_id']})")
                print(f"  Old price: ${token['current_price']}")
                print(f"  New price: ${actual_price}")
                print(f"  Old ROI: {token['roi_percent']:.1f}%")
                print(f"  New ROI: {correct_roi:.1f}%")
                
                # Update
                update_result = supabase.table('crypto_calls').update({
                    'current_price': actual_price,
                    'roi_percent': correct_roi
                }).eq('krom_id', token['krom_id']).execute()
                
                print("  ✅ Fixed!\n")

# Now check for other tokens with contract addresses and suspicious ROI
print("\n=== CHECKING OTHER TOKENS WITH CONTRACTS ===\n")

# Get tokens with contracts and ROI > 200%
suspicious = supabase.table('crypto_calls').select('krom_id, ticker, contract_address, network, price_at_call, current_price, roi_percent').not_.is_('contract_address', 'null').gt('roi_percent', 200).order('roi_percent', desc=True).limit(50).execute()

print(f"Found {len(suspicious.data)} tokens with contracts and >200% ROI\n")

fixed_count = 0
network_map = {
    'ethereum': 'eth',
    'solana': 'solana',
    'bsc': 'bsc',
    'polygon': 'polygon',
    'arbitrum': 'arbitrum',
    'base': 'base'
}

for token in suspicious.data:
    print(f"Checking {token['ticker']} (ROI: {token['roi_percent']:.1f}%)...")
    
    # Try DexScreener first
    try:
        response = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{token['contract_address']}")
        actual_price = None
        
        if response.status_code == 200:
            data = response.json()
            if data.get('pairs') and len(data['pairs']) > 0:
                actual_price = float(data['pairs'][0]['priceUsd'])
        
        # If not found on DexScreener, try GeckoTerminal
        if actual_price is None and token['network']:
            api_network = network_map.get(token['network'], token['network'])
            gecko_response = requests.get(f"https://api.geckoterminal.com/api/v2/networks/{api_network}/tokens/{token['contract_address']}/pools")
            
            if gecko_response.status_code == 200:
                gecko_data = gecko_response.json()
                if gecko_data.get('data') and len(gecko_data['data']) > 0:
                    pool_price = gecko_data['data'][0]['attributes'].get('token_price_usd')
                    if pool_price:
                        actual_price = float(pool_price)
        
        if actual_price and actual_price > 0:
            db_price = token['current_price']
            price_ratio = db_price / actual_price
            
            # If price is more than 10x off, it's likely wrong
            if price_ratio > 10 or price_ratio < 0.1:
                print(f"  ❌ WRONG PRICE!")
                print(f"     DB: ${db_price} vs Actual: ${actual_price} (ratio: {price_ratio:.1f}x)")
                
                # Calculate correct ROI
                correct_roi = ((actual_price - token['price_at_call']) / token['price_at_call']) * 100
                
                # Update
                update_result = supabase.table('crypto_calls').update({
                    'current_price': actual_price,
                    'roi_percent': correct_roi
                }).eq('krom_id', token['krom_id']).execute()
                
                print(f"     ✅ Fixed! New ROI: {correct_roi:.1f}%\n")
                fixed_count += 1
            else:
                print(f"  ✓ Price looks OK\n")
        else:
            print(f"  ⚠️  Could not fetch price\n")
            
        time.sleep(0.3)  # Rate limit
        
    except Exception as e:
        print(f"  Error: {e}\n")

print(f"\n=== SUMMARY ===")
print(f"Fixed {fixed_count + 1} incorrect prices (including OZZY)")
