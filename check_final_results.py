#!/usr/bin/env python3
"""
Check final results after batch processing
"""

import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(supabase_url, supabase_key)

# Get stats
total = supabase.table('token_discovery').select('id', count='exact').execute()
websites = supabase.table('token_discovery').select('id', count='exact').not_.is_('website_url', 'null').execute()
twitter = supabase.table('token_discovery').select('id', count='exact').not_.is_('twitter_url', 'null').execute()
telegram = supabase.table('token_discovery').select('id', count='exact').not_.is_('telegram_url', 'null').execute()
discord = supabase.table('token_discovery').select('id', count='exact').not_.is_('discord_url', 'null').execute()
unchecked = supabase.table('token_discovery').select('id', count='exact').is_('website_checked_at', 'null').execute()

print('📊 FINAL RESULTS AFTER BATCH PROCESSING')
print('='*60)
print(f'Total tokens in database: {total.count:,}')
print(f'Tokens never checked: {unchecked.count:,}')
print('')
print(f'🌐 Tokens with websites: {websites.count} ({websites.count/total.count*100:.2f}%)')
print(f'🐦 Tokens with Twitter: {twitter.count}')
print(f'💬 Tokens with Telegram: {telegram.count}')
print(f'💭 Tokens with Discord: {discord.count}')
print('')

# Get some examples of tokens with websites
examples = supabase.table('token_discovery')\
    .select('symbol, network, website_url, initial_liquidity_usd')\
    .not_.is_('website_url', 'null')\
    .order('initial_liquidity_usd', desc=True)\
    .limit(10)\
    .execute()

print('Top 10 tokens with websites (by liquidity):')
for token in examples.data:
    liq = f"${token['initial_liquidity_usd']:,.0f}" if token.get('initial_liquidity_usd') else 'N/A'
    print(f"  • {token['symbol']} ({token['network']}): {liq} - {token['website_url']}")