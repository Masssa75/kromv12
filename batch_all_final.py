#!/usr/bin/env python3
"""
Final batch processor - check ALL tokens for websites
Optimized for speed and reliability
"""

import os
import requests
import time
from datetime import datetime

# Load env vars directly
from pathlib import Path
env_path = Path('.env')
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            if '=' in line and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value

from supabase import create_client

supabase_url = os.environ.get('SUPABASE_URL')
supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(supabase_url, supabase_key)

print('🚀 BATCH CHECKING ALL TOKENS FOR WEBSITES')
print(f'⏰ Started: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('='*70)

# Get total count
count_result = supabase.table('token_discovery')\
    .select('id', count='exact')\
    .is_('website_url', 'null')\
    .execute()

total_to_process = count_result.count
print(f'📊 Total tokens without websites: {total_to_process:,}')
print(f'📦 Estimated API calls: {total_to_process // 30:,}')
print(f'⏱️ Estimated time: {total_to_process // 30 * 0.3 / 60:.1f} minutes\n')

# Process all tokens
offset = 0
batch_size = 300  # Process 300 at a time
total_checked = 0
websites_found = 0
twitter_found = 0
telegram_found = 0
api_calls = 0
start_time = time.time()

while offset < total_to_process:
    # Get batch of tokens
    print(f'Fetching tokens {offset+1}-{min(offset+batch_size, total_to_process)}...')
    
    tokens = supabase.table('token_discovery')\
        .select('id, contract_address, symbol, network')\
        .is_('website_url', 'null')\
        .limit(batch_size)\
        .range(offset, offset + batch_size - 1)\
        .execute()
    
    if not tokens.data:
        break
    
    # Process in groups of 30 for DexScreener API
    for i in range(0, len(tokens.data), 30):
        group = tokens.data[i:i+30]
        addresses = [t['contract_address'] for t in group]
        
        try:
            # Call DexScreener batch API
            response = requests.get(
                f'https://api.dexscreener.com/latest/dex/tokens/{",".join(addresses)}',
                headers={'Accept': 'application/json'},
                timeout=15
            )
            api_calls += 1
            
            if response.status_code == 200:
                data = response.json()
                
                # Process each token
                for token in group:
                    update_data = {'website_checked_at': datetime.now().isoformat()}
                    found_info = False
                    
                    # Find data for this token
                    if 'pairs' in data:
                        for pair in data['pairs']:
                            if pair.get('baseToken', {}).get('address', '').lower() == token['contract_address'].lower():
                                info = pair.get('info', {})
                                
                                # Check for website
                                if info and info.get('websites'):
                                    update_data['website_url'] = info['websites'][0].get('url')
                                    websites_found += 1
                                    found_info = True
                                    print(f'  ✅ {token["symbol"]} ({token["network"]}): Website found!')
                                
                                # Check for socials
                                if info and info.get('socials'):
                                    for social in info['socials']:
                                        if social['type'] == 'twitter':
                                            update_data['twitter_url'] = social.get('url')
                                            twitter_found += 1
                                        elif social['type'] == 'telegram':
                                            update_data['telegram_url'] = social.get('url')
                                            telegram_found += 1
                                        elif social['type'] == 'discord':
                                            update_data['discord_url'] = social.get('url')
                                
                                if found_info:
                                    break
                    
                    # Update database
                    try:
                        supabase.table('token_discovery')\
                            .update(update_data)\
                            .eq('id', token['id'])\
                            .execute()
                        total_checked += 1
                    except Exception as e:
                        print(f'  Error updating {token["symbol"]}: {e}')
            
        except Exception as e:
            print(f'  API error: {e}')
        
        # Rate limiting
        time.sleep(0.3)
    
    # Progress update
    elapsed = time.time() - start_time
    rate = total_checked / elapsed if elapsed > 0 else 0
    remaining = (total_to_process - total_checked) / rate if rate > 0 else 0
    
    print(f'Progress: {total_checked:,}/{total_to_process:,} ({total_checked/total_to_process*100:.1f}%) | '
          f'Websites: {websites_found} | API: {api_calls} | '
          f'ETA: {remaining/60:.1f} min\n')
    
    offset += batch_size

# Final summary
elapsed_total = time.time() - start_time
print('\n' + '='*70)
print('✅ BATCH PROCESSING COMPLETE')
print(f'⏰ Finished: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print(f'⏱️ Total time: {elapsed_total/60:.1f} minutes\n')

print('📊 RESULTS:')
print(f'  Tokens checked: {total_checked:,}')
print(f'  Websites found: {websites_found}')
print(f'  Twitter links: {twitter_found}')
print(f'  Telegram links: {telegram_found}')
print(f'  API calls made: {api_calls:,}')
print(f'  Average speed: {total_checked/elapsed_total:.1f} tokens/second')

# Get final database totals
final_websites = supabase.table('token_discovery').select('id', count='exact').not_.is_('website_url', 'null').execute()
print(f'\n📊 TOTAL TOKENS WITH WEBSITES IN DATABASE: {final_websites.count}')