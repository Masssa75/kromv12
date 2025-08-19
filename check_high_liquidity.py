#!/usr/bin/env python3
"""
Check high liquidity tokens for websites
"""

import os
import requests
import time
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime

load_dotenv()

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(supabase_url, supabase_key)

print('🚀 Checking high liquidity tokens for websites')
print('='*50)

# Get tokens with high liquidity that don't have websites
tokens = supabase.table('token_discovery')\
    .select('id, contract_address, symbol, network, initial_liquidity_usd')\
    .is_('website_url', 'null')\
    .gt('initial_liquidity_usd', 50000)\
    .order('initial_liquidity_usd', desc=True)\
    .limit(300)\
    .execute()

print(f'Found {len(tokens.data)} tokens with >$50k liquidity without websites')
print('Processing in batches of 30...\n')

total_checked = 0
websites_found = 0
twitter_found = 0
telegram_found = 0

# Process in batches of 30
for i in range(0, len(tokens.data), 30):
    batch = tokens.data[i:i+30]
    addresses = [t['contract_address'] for t in batch]
    address_list = ','.join(addresses)
    
    try:
        response = requests.get(
            f'https://api.dexscreener.com/latest/dex/tokens/{address_list}',
            headers={'Accept': 'application/json'},
            timeout=10
        )
        data = response.json()
        
        if 'pairs' in data:
            for token in batch:
                pairs = [p for p in data['pairs'] 
                        if p.get('baseToken', {}).get('address', '').lower() == token['contract_address'].lower()]
                
                update_data = {'website_checked_at': datetime.now().isoformat()}
                
                for pair in pairs:
                    info = pair.get('info', {})
                    if info:
                        websites = info.get('websites', [])
                        if websites:
                            update_data['website_url'] = websites[0].get('url')
                            websites_found += 1
                            liq = f"${token['initial_liquidity_usd']:,.0f}"
                            print(f'  ✅ {token["symbol"]} ({liq}): {websites[0].get("url")}')
                        
                        socials = info.get('socials', [])
                        for social in socials:
                            if social['type'] == 'twitter':
                                update_data['twitter_url'] = social.get('url')
                                twitter_found += 1
                            elif social['type'] == 'telegram':
                                update_data['telegram_url'] = social.get('url')
                                telegram_found += 1
                        
                        if 'website_url' in update_data:
                            break
                
                # Update database
                supabase.table('token_discovery').update(update_data).eq('id', token['id']).execute()
                total_checked += 1
        
        print(f'Batch {i//30 + 1}/{(len(tokens.data)+29)//30}: Checked {len(batch)} tokens, {websites_found} websites so far')
    except Exception as e:
        print(f'Error: {e}')
    
    time.sleep(0.5)  # Rate limiting

print(f'\n' + '='*50)
print(f'✅ Checked {total_checked} high-liquidity tokens')
print(f'🌐 Found {websites_found} websites ({websites_found/total_checked*100:.1f}%)')
print(f'🐦 Found {twitter_found} Twitter links')
print(f'💬 Found {telegram_found} Telegram links')

# Final count
final = supabase.table('token_discovery').select('*', count='exact').not_.is_('website_url', 'null').execute()
print(f'\n📊 Total tokens with websites in database: {final.count}')