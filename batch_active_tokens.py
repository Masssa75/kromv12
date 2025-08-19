#!/usr/bin/env python3
"""
Check websites for ACTIVE tokens only (with liquidity or recent)
"""

import os
import time
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Initialize Supabase
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(supabase_url, supabase_key)

def check_token_batch(addresses):
    """Check a batch of up to 30 tokens using DexScreener batch API"""
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

print("🚀 Active Token Website Checker")
print(f"⏰ Started: {datetime.now().strftime('%H:%M:%S')}")
print("="*60)

# Focus on tokens that are likely active:
# 1. Recent tokens (last 48 hours)
# 2. Tokens with significant liquidity (>$5000)

two_days_ago = (datetime.now() - timedelta(hours=48)).isoformat()

print("📊 Fetching active tokens...")
print("   Criteria: Added in last 48h OR liquidity > $5,000")

# Get recent tokens without websites
recent = supabase.table('token_discovery')\
    .select('id, contract_address, symbol, network, initial_liquidity_usd')\
    .is_('website_url', 'null')\
    .gte('first_seen_at', two_days_ago)\
    .limit(3000)\
    .execute()

print(f"   Found {len(recent.data)} recent tokens (last 48h)")

# Get high liquidity tokens without websites
high_liq = supabase.table('token_discovery')\
    .select('id, contract_address, symbol, network, initial_liquidity_usd')\
    .is_('website_url', 'null')\
    .gt('initial_liquidity_usd', 5000)\
    .order('initial_liquidity_usd', desc=True)\
    .limit(1000)\
    .execute()

print(f"   Found {len(high_liq.data)} high liquidity tokens (>$5k)")

# Combine and deduplicate
seen_ids = set()
active_tokens = []

for token in recent.data:
    if token['id'] not in seen_ids:
        seen_ids.add(token['id'])
        active_tokens.append(token)

for token in high_liq.data:
    if token['id'] not in seen_ids:
        seen_ids.add(token['id'])
        active_tokens.append(token)

print(f"\n✅ Total active tokens to check: {len(active_tokens)}")
print(f"⏱️ Estimated time: {len(active_tokens)/30/2:.1f} minutes")
print("")

total_checked = 0
websites_found = 0
twitter_found = 0
telegram_found = 0
no_data_count = 0
start_time = time.time()

# Process in batches of 30
for i in range(0, len(active_tokens), 30):
    batch = active_tokens[i:i+30]
    addresses = [t['contract_address'] for t in batch]
    
    # Check with DexScreener
    data = check_token_batch(addresses)
    
    if data and 'pairs' in data:
        batch_found = 0
        
        for token in batch:
            # Find matching pairs
            pairs = [p for p in data['pairs'] 
                    if p.get('baseToken', {}).get('address', '').lower() == token['contract_address'].lower()]
            
            if not pairs:
                no_data_count += 1
                continue
            
            update_data = {'website_checked_at': datetime.now().isoformat()}
            
            for pair in pairs:
                info = pair.get('info', {})
                if not info:
                    continue
                
                # Extract website
                websites = info.get('websites', [])
                if websites and 'website_url' not in update_data:
                    update_data['website_url'] = websites[0].get('url')
                    websites_found += 1
                    batch_found += 1
                    liq = f"${token['initial_liquidity_usd']:,.0f}" if token.get('initial_liquidity_usd') else "Unknown"
                    print(f"  ✅ {token['symbol']} ({liq}): {websites[0].get('url')}")
                
                # Extract socials
                for social in info.get('socials', []):
                    if social['type'] == 'twitter' and 'twitter_url' not in update_data:
                        update_data['twitter_url'] = social['url']
                        twitter_found += 1
                    elif social['type'] == 'telegram' and 'telegram_url' not in update_data:
                        update_data['telegram_url'] = social['url']
                        telegram_found += 1
                    elif social['type'] == 'discord' and 'discord_url' not in update_data:
                        update_data['discord_url'] = social['url']
                
                if 'website_url' in update_data:
                    break
            
            # Update database
            try:
                supabase.table('token_discovery').update(update_data).eq('id', token['id']).execute()
                total_checked += 1
            except:
                pass
        
        # Progress every 10 batches
        if (i // 30) % 10 == 0 and i > 0:
            elapsed = time.time() - start_time
            rate = total_checked / elapsed if elapsed > 0 else 0
            dead_rate = no_data_count / total_checked * 100 if total_checked > 0 else 0
            print(f"\n  Progress: {total_checked}/{len(active_tokens)} | "
                  f"Websites: {websites_found} | Dead: {dead_rate:.0f}% | "
                  f"Speed: {rate:.1f}/s")
    
    # Rate limiting
    time.sleep(0.5)

# Summary
elapsed = time.time() - start_time
print("\n" + "="*60)
print("✅ COMPLETE")
print(f"⏱️ Time: {elapsed/60:.1f} minutes")
print(f"\n📊 Results:")
print(f"   Tokens checked: {total_checked}")
print(f"   Websites found: {websites_found} ({websites_found/total_checked*100:.1f}%)")
print(f"   Twitter links: {twitter_found}")
print(f"   Telegram links: {telegram_found}")
print(f"   Dead tokens (no data): {no_data_count} ({no_data_count/total_checked*100:.1f}%)")

# Final database stats
final = supabase.table('token_discovery').select('*', count='exact').not_.is_('website_url', 'null').execute()
print(f"\n📊 Total tokens with websites in database: {final.count}")