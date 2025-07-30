import os
from supabase import create_client, Client
from dotenv import load_dotenv
import requests
import time

load_dotenv()

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

print("=== ANALYZING PRICE SOURCES ===")
print("Testing which tokens use DexScreener vs GeckoTerminal\n")

# Get a sample of recently updated tokens
recent = supabase.table('crypto_calls').select(
    'ticker, contract_address, network, current_price, roi_percent, price_updated_at'
).not_.is_('current_price', 'null').not_.is_('contract_address', 'null').order('price_updated_at', desc=True).limit(20).execute()

print(f"Testing {len(recent.data)} recently updated tokens...\n")

dexscreener_count = 0
gecko_count = 0
wrong_prices = []

for token in recent.data:
    # Test DexScreener
    response = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{token['contract_address']}")
    dexscreener_price = None
    
    if response.status_code == 200:
        data = response.json()
        if data.get('pairs') and len(data['pairs']) > 0:
            dexscreener_price = float(data['pairs'][0]['priceUsd'])
            dexscreener_count += 1
    
    # Test GeckoTerminal
    gecko_price = None
    if token['network']:
        network_map = {'ethereum': 'eth', 'solana': 'solana', 'bsc': 'bsc'}
        api_network = network_map.get(token['network'], token['network'])
        
        time.sleep(0.3)  # Rate limit
        gecko_response = requests.get(f"https://api.geckoterminal.com/api/v2/networks/{api_network}/tokens/{token['contract_address']}/pools")
        
        if gecko_response.status_code == 200:
            gecko_data = gecko_response.json()
            if gecko_data.get('data') and len(gecko_data['data']) > 0:
                pool_price = gecko_data['data'][0]['attributes'].get('token_price_usd')
                if pool_price:
                    gecko_price = float(pool_price)
                    if not dexscreener_price:  # Only count if DexScreener didn't have it
                        gecko_count += 1
    
    # Compare prices
    db_price = token['current_price']
    
    print(f"{token['ticker']}:")
    print(f"  DB Price: ${db_price}")
    if dexscreener_price:
        print(f"  DexScreener: ${dexscreener_price}")
    if gecko_price:
        print(f"  GeckoTerminal: ${gecko_price}")
    
    # Check which is closer to DB price
    if dexscreener_price and gecko_price:
        dex_diff = abs(db_price - dexscreener_price) / dexscreener_price * 100
        gecko_diff = abs(db_price - gecko_price) / gecko_price * 100
        
        if dex_diff < 5:
            print(f"  ✅ DexScreener matches DB (diff: {dex_diff:.1f}%)")
        elif gecko_diff < 5:
            print(f"  ✅ GeckoTerminal matches DB (diff: {gecko_diff:.1f}%)")
        else:
            print(f"  ❌ Neither matches well (DexDiff: {dex_diff:.0f}%, GeckoDiff: {gecko_diff:.0f}%)")
            wrong_prices.append({
                'ticker': token['ticker'],
                'db': db_price,
                'dex': dexscreener_price,
                'gecko': gecko_price
            })
    elif dexscreener_price:
        diff = abs(db_price - dexscreener_price) / dexscreener_price * 100
        if diff > 10:
            print(f"  ❌ Wrong price? DB differs {diff:.0f}% from DexScreener")
            wrong_prices.append({'ticker': token['ticker'], 'db': db_price, 'dex': dexscreener_price})
    elif gecko_price:
        diff = abs(db_price - gecko_price) / gecko_price * 100
        if diff > 10:
            print(f"  ❌ Wrong price? DB differs {diff:.0f}% from GeckoTerminal")
            wrong_prices.append({'ticker': token['ticker'], 'db': db_price, 'gecko': gecko_price})
    
    print()

print(f"\n=== SUMMARY ===")
print(f"Found on DexScreener: {dexscreener_count}")
print(f"Only on GeckoTerminal: {gecko_count}")
print(f"Potentially wrong prices: {len(wrong_prices)}")

if wrong_prices:
    print("\nTokens with suspicious prices:")
    for wp in wrong_prices[:5]:
        print(f"  {wp['ticker']}: DB=${wp['db']}")
        if 'dex' in wp:
            print(f"    DexScreener: ${wp['dex']}")
        if 'gecko' in wp:
            print(f"    GeckoTerminal: ${wp['gecko']}")
