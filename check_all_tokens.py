#!/usr/bin/env python3
"""
Check ALL tokens for websites - full batch processing
"""

import os
import requests
import time
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

print('🚀 FULL TOKEN WEBSITE CHECK - ALL TOKENS')
print(f'⏰ Started: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print('='*70)

# Get total count
count_result = supabase.table('token_discovery')\
    .select('*', count='exact')\
    .is_('website_url', 'null')\
    .execute()

total_to_check = count_result.count
print(f'📊 Total tokens without websites: {total_to_check:,}')
print(f'📦 Will process in {(total_to_check + 29) // 30:,} API calls (30 tokens each)')
print(f'⏱️ Estimated time: {total_to_check / 30 * 0.5 / 60:.1f} minutes (2 calls/second)')
print('')

# Process in chunks to avoid memory issues
chunk_size = 1000
offset = 0

total_checked = 0
websites_found = 0
twitter_found = 0
telegram_found = 0
discord_found = 0
tokens_with_data = 0
api_calls = 0
start_time = time.time()

print('Starting batch processing...\n')

while offset < total_to_check:
    # Fetch next chunk
    tokens = supabase.table('token_discovery')\
        .select('id, contract_address, symbol, network, initial_liquidity_usd')\
        .is_('website_url', 'null')\
        .range(offset, min(offset + chunk_size - 1, total_to_check))\
        .execute()
    
    if not tokens.data:
        break
    
    # Process this chunk in batches of 30
    for i in range(0, len(tokens.data), 30):
        batch = tokens.data[i:i+30]
        addresses = [t['contract_address'] for t in batch]
        
        # Call DexScreener API
        data = check_token_batch(addresses)
        api_calls += 1
        
        if data and 'pairs' in data:
            for token in batch:
                # Find matching pairs
                pairs = [p for p in data['pairs'] 
                        if p.get('baseToken', {}).get('address', '').lower() == token['contract_address'].lower()]
                
                if pairs:
                    tokens_with_data += 1
                
                update_data = {'website_checked_at': datetime.now().isoformat()}
                found_info = False
                
                for pair in pairs:
                    info = pair.get('info', {})
                    if info:
                        # Check for website
                        websites = info.get('websites', [])
                        if websites and 'website_url' not in update_data:
                            update_data['website_url'] = websites[0].get('url')
                            websites_found += 1
                            found_info = True
                            liq = f"${token['initial_liquidity_usd']:,.0f}" if token.get('initial_liquidity_usd') else "N/A"
                            print(f'  ✅ Website: {token["symbol"]} ({token["network"]}, {liq})')
                        
                        # Check for socials
                        socials = info.get('socials', [])
                        for social in socials:
                            if social['type'] == 'twitter' and 'twitter_url' not in update_data:
                                update_data['twitter_url'] = social.get('url')
                                twitter_found += 1
                                found_info = True
                            elif social['type'] == 'telegram' and 'telegram_url' not in update_data:
                                update_data['telegram_url'] = social.get('url')
                                telegram_found += 1
                                found_info = True
                            elif social['type'] == 'discord' and 'discord_url' not in update_data:
                                update_data['discord_url'] = social.get('url')
                                discord_found += 1
                                found_info = True
                        
                        if found_info:
                            break
                
                # Update database
                try:
                    supabase.table('token_discovery').update(update_data).eq('id', token['id']).execute()
                    total_checked += 1
                except:
                    pass
        
        # Progress update every 100 API calls
        if api_calls % 100 == 0:
            elapsed = time.time() - start_time
            rate = total_checked / elapsed if elapsed > 0 else 0
            eta = (total_to_check - total_checked) / rate if rate > 0 else 0
            dead_pct = (1 - tokens_with_data / total_checked) * 100 if total_checked > 0 else 0
            
            print(f'\n📈 Progress Report #{api_calls // 100}')
            print(f'   Checked: {total_checked:,}/{total_to_check:,} ({total_checked/total_to_check*100:.1f}%)')
            print(f'   Websites: {websites_found} | Twitter: {twitter_found} | Telegram: {telegram_found}')
            print(f'   Dead tokens: {dead_pct:.1f}% | Speed: {rate:.1f}/sec | ETA: {eta/60:.1f} min')
            print('')
        
        # Rate limiting - 2 requests per second
        time.sleep(0.5)
    
    offset += chunk_size

# Final summary
elapsed = time.time() - start_time
print('\n' + '='*70)
print('✅ FULL BATCH PROCESSING COMPLETE')
print(f'⏰ Finished: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
print(f'⏱️ Total time: {elapsed/60:.1f} minutes')
print('')
print('📊 RESULTS:')
print(f'   Tokens checked: {total_checked:,}')
print(f'   Tokens with data: {tokens_with_data:,} ({tokens_with_data/total_checked*100:.1f}%)')
print(f'   Dead tokens: {total_checked - tokens_with_data:,} ({(total_checked - tokens_with_data)/total_checked*100:.1f}%)')
print('')
print(f'   🌐 Websites found: {websites_found}')
print(f'   🐦 Twitter links: {twitter_found}')
print(f'   💬 Telegram links: {telegram_found}')
print(f'   💭 Discord links: {discord_found}')
print('')
print(f'   API calls made: {api_calls:,}')
print(f'   Average speed: {total_checked/elapsed:.1f} tokens/second')

# Final database stats
print('\n📊 FINAL DATABASE TOTALS:')
final_websites = supabase.table('token_discovery').select('*', count='exact').not_.is_('website_url', 'null').execute()
final_twitter = supabase.table('token_discovery').select('*', count='exact').not_.is_('twitter_url', 'null').execute()
final_telegram = supabase.table('token_discovery').select('*', count='exact').not_.is_('telegram_url', 'null').execute()
final_discord = supabase.table('token_discovery').select('*', count='exact').not_.is_('discord_url', 'null').execute()

print(f'   Tokens with websites: {final_websites.count}')
print(f'   Tokens with Twitter: {final_twitter.count}')
print(f'   Tokens with Telegram: {final_telegram.count}')
print(f'   Tokens with Discord: {final_discord.count}')