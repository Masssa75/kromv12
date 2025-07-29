#!/usr/bin/env python3
"""
Update one token at a time - simple and reliable
"""
import os
import sys
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json"
}

# Network mapping
NETWORK_MAP = {
    'ethereum': 'eth',
    'solana': 'solana',
    'bsc': 'bsc',
    'polygon': 'polygon',
    'arbitrum': 'arbitrum',
    'base': 'base'
}

# Get ONE token
query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id,ticker,contract_address,network,price_at_call&current_price.is.null&contract_address.not.is.null&network.not.is.null&price_at_call.gt.0&order=created_at.asc&limit=1"

resp = requests.get(query, headers=headers)
if resp.status_code != 200:
    print(f"❌ Query failed: {resp.status_code}")
    sys.exit(1)

tokens = resp.json()
if not tokens:
    print("✅ No more tokens to process!")
    sys.exit(0)

token = tokens[0]
print(f"Processing: {token['ticker']} ({token['network']})")
print(f"Contract: {token['contract_address']}")

# Try DexScreener
price = None
source = None

try:
    resp = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{token['contract_address']}")
    data = resp.json()
    if data.get('pairs') and len(data['pairs']) > 0:
        price = float(data['pairs'][0]['priceUsd'])
        source = "DexScreener"
except:
    pass

# Try GeckoTerminal if no price yet
if price is None:
    try:
        api_network = NETWORK_MAP.get(token['network'], token['network'])
        resp = requests.get(f"https://api.geckoterminal.com/api/v2/networks/{api_network}/tokens/{token['contract_address']}")
        data = resp.json()
        if data.get('data') and data['data'].get('attributes'):
            price_str = data['data']['attributes'].get('price_usd')
            if price_str:
                price = float(price_str)
                source = "GeckoTerminal"
    except:
        pass

if price:
    print(f"Found price: ${price:.8f} (via {source})")
    
    # Update database
    update_url = f"{SUPABASE_URL}/rest/v1/crypto_calls?id=eq.{token['id']}"
    update_data = {
        "current_price": price,
        "price_updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    resp = requests.patch(update_url, json=update_data, headers=headers)
    if resp.status_code in [200, 204]:
        print("✅ Updated successfully")
    else:
        print(f"❌ Update failed: {resp.status_code}")
else:
    print("❌ No price found on any platform")