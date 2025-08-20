#!/usr/bin/env python3
import os
import requests
from supabase import create_client
from dotenv import load_dotenv
import time

load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(supabase_url, supabase_key)

print("Updating social data for gecko_trending tokens...")

# Get all gecko_trending tokens without social data
result = supabase.table('crypto_calls').select('id,ticker,network,pool_address').eq('source', 'gecko_trending').is_('website_url', 'null').execute()

tokens = result.data
print(f"Found {len(tokens)} tokens without social data")

for token in tokens:
    if not token['pool_address']:
        print(f"Skipping {token['ticker']} - no pool address")
        continue
        
    print(f"Fetching social data for {token['ticker']} on {token['network']}...")
    
    # Fetch from DexScreener
    try:
        response = requests.get(
            f"https://api.dexscreener.com/latest/dex/pairs/{token['network']}/{token['pool_address']}",
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        
        if response.status_code == 200:
            data = response.json()
            pair = data.get('pairs', [{}])[0] if 'pairs' in data else data.get('pair', {})
            
            if pair and 'info' in pair:
                info = pair['info']
                update_data = {}
                
                # Extract website
                if 'websites' in info and info['websites']:
                    website = info['websites'][0]
                    update_data['website_url'] = website['url'] if isinstance(website, dict) else website
                
                # Extract socials
                if 'socials' in info:
                    for social in info['socials']:
                        if social['type'] == 'twitter':
                            update_data['twitter_url'] = social['url']
                        elif social['type'] == 'telegram':
                            update_data['telegram_url'] = social['url']
                        elif social['type'] == 'discord':
                            update_data['discord_url'] = social['url']
                
                if update_data:
                    update_data['socials_fetched_at'] = 'now()'
                    supabase.table('crypto_calls').update(update_data).eq('id', token['id']).execute()
                    print(f"  ✅ Updated {token['ticker']}: {list(update_data.keys())}")
                else:
                    print(f"  ⚠️ No social data found for {token['ticker']}")
        
        time.sleep(0.2)  # Rate limit
        
    except Exception as e:
        print(f"  ❌ Error fetching {token['ticker']}: {e}")

print("\nDone!")