#!/usr/bin/env python3
"""
Stream processing all tokens - starts immediately
"""

import os
import requests
import time
import sys
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(supabase_url, supabase_key)

def check_token_batch(addresses):
    """Check a batch of up to 30 tokens using DexScreener API"""
    try:
        address_list = ','.join(addresses[:30])
        response = requests.get(
            f'https://api.dexscreener.com/latest/dex/tokens/{address_list}',
            headers={'Accept': 'application/json'},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

print('🚀 STREAMING TOKEN CHECKER - Processing immediately')
print(f'⏰ Started: {datetime.now().strftime("%H:%M:%S")}')
print('='*60)

# Quick count
print('Getting total count...')
count_result = supabase.table('token_discovery')\
    .select('id', count='exact')\
    .is_('website_url', 'null')\
    .execute()

total_to_check = count_result.count
print(f'📊 Total tokens to check: {total_to_check:,}')
print(f'📦 Will make ~{total_to_check // 30:,} API calls')
print('')

# Process in small chunks
chunk_size = 300  # Small chunks for quick start
offset = 0

total_checked = 0
websites_found = 0
twitter_found = 0
telegram_found = 0
api_calls = 0
start_time = time.time()

print('Processing tokens...\n')
sys.stdout.flush()

while offset < total_to_check:
    # Fetch small chunk
    tokens = supabase.table('token_discovery')\
        .select('id, contract_address, symbol, network')\
        .is_('website_url', 'null')\
        .range(offset, min(offset + chunk_size - 1, total_to_check))\
        .execute()
    
    if not tokens.data:
        break
    
    # Process in batches of 30
    for i in range(0, len(tokens.data), 30):
        batch = tokens.data[i:i+30]
        addresses = [t['contract_address'] for t in batch]
        
        # Call API
        data = check_token_batch(addresses)
        api_calls += 1
        
        if data and 'pairs' in data:
            for token in batch:
                pairs = [p for p in data['pairs'] 
                        if p.get('baseToken', {}).get('address', '').lower() == token['contract_address'].lower()]
                
                update_data = {'website_checked_at': datetime.now().isoformat()}
                
                for pair in pairs:
                    info = pair.get('info', {})
                    if info:
                        # Check for website
                        websites = info.get('websites', [])
                        if websites:
                            update_data['website_url'] = websites[0].get('url')
                            websites_found += 1
                            print(f'  ✅ {token["symbol"]}: Found website!')
                            sys.stdout.flush()
                        
                        # Socials
                        for social in info.get('socials', []):
                            if social['type'] == 'twitter':
                                update_data['twitter_url'] = social.get('url')
                                twitter_found += 1
                            elif social['type'] == 'telegram':
                                update_data['telegram_url'] = social.get('url')
                                telegram_found += 1
                        
                        break
                
                # Update database
                try:
                    supabase.table('token_discovery').update(update_data).eq('id', token['id']).execute()
                    total_checked += 1
                except:
                    pass
        
        # Quick progress every 50 calls
        if api_calls % 50 == 0:
            elapsed = time.time() - start_time
            rate = total_checked / elapsed if elapsed > 0 else 0
            print(f'Progress: {total_checked:,}/{total_to_check:,} | '
                  f'Websites: {websites_found} | '
                  f'Speed: {rate:.0f}/s | '
                  f'API: {api_calls}')
            sys.stdout.flush()
        
        time.sleep(0.3)  # Slightly faster
    
    offset += chunk_size

# Summary
elapsed = time.time() - start_time
print('\n' + '='*60)
print(f'✅ COMPLETE in {elapsed/60:.1f} minutes')
print(f'Checked: {total_checked:,} tokens')
print(f'Websites: {websites_found}')
print(f'Twitter: {twitter_found}')
print(f'Telegram: {telegram_found}')
print(f'API calls: {api_calls:,}')