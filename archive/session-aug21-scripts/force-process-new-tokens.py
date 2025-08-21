#!/usr/bin/env python3
"""
Force the ultra-tracker to process tokens that have never been checked
"""

import os
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Initialize Supabase client with service role key
url = os.getenv("SUPABASE_URL")
service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, service_key)

print("Finding tokens that have never been processed...")

# Get tokens with NULL ath_last_checked and good liquidity
response = supabase.table("crypto_calls").select(
    "id, ticker, pool_address, network, circulating_supply"
).is_("ath_last_checked", None).gte("liquidity_usd", 20000).eq("is_dead", False).limit(50).execute()

unprocessed = response.data
print(f"Found {len(unprocessed)} unprocessed tokens with >$20K liquidity")

# Process each token manually
for token in unprocessed[:10]:  # Do first 10
    print(f"\nProcessing {token['ticker']}...")
    
    # Map network names
    network_map = {
        'ethereum': 'ethereum',
        'solana': 'solana',
        'bsc': 'bsc',
        'base': 'base',
        'arbitrum': 'arbitrum',
        'polygon': 'polygon'
    }
    
    dex_network = network_map.get(token['network'], token['network'])
    
    # Fetch from DexScreener
    try:
        url = f"https://api.dexscreener.com/latest/dex/pairs/{dex_network}/{token['pool_address']}"
        resp = requests.get(url)
        data = resp.json()
        
        if data.get('pairs') and len(data['pairs']) > 0:
            pair = data['pairs'][0]
            
            current_price = float(pair.get('priceUsd', 0))
            liquidity = float(pair.get('liquidity', {}).get('usd', 0))
            volume_24h = float(pair.get('volume', {}).get('h24', 0))
            
            # Calculate market cap
            current_market_cap = None
            if token['circulating_supply'] and current_price > 0:
                current_market_cap = current_price * token['circulating_supply']
            
            # Update the token
            update_data = {
                "current_price": current_price,
                "current_market_cap": current_market_cap,
                "liquidity_usd": liquidity,
                "volume_24h": volume_24h,
                "ath_last_checked": datetime.utcnow().isoformat(),
                "price_updated_at": datetime.utcnow().isoformat()
            }
            
            update_resp = supabase.table("crypto_calls").update(
                update_data
            ).eq("id", token['id']).execute()
            
            if update_resp.data:
                print(f"✅ {token['ticker']}: price=${current_price:.6f}, MC=${current_market_cap:,.0f}" if current_market_cap else f"✅ {token['ticker']}: price=${current_price:.6f}")
            else:
                print(f"❌ Failed to update {token['ticker']}")
        else:
            print(f"⚠️ {token['ticker']}: Not found on DexScreener")
    except Exception as e:
        print(f"❌ Error processing {token['ticker']}: {e}")

print("\n✅ Processing complete!")