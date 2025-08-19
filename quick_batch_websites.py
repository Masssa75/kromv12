#!/usr/bin/env python3
"""
Quick batch check for websites - processes first 1000 tokens as a test
"""

import os
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Initialize Supabase
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(supabase_url, supabase_key)

def check_token_batch(addresses):
    """Check a batch of tokens for websites using DexScreener API"""
    try:
        address_list = ','.join(addresses)
        response = requests.get(
            f'https://api.dexscreener.com/latest/dex/tokens/{address_list}',
            headers={'Accept': 'application/json'},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error: {e}")
    return None

print("🚀 Quick Batch Website Checker")
print(f"Time: {datetime.now().strftime('%H:%M:%S')}")
print("="*60)

# Get first 1000 tokens without websites
print("📥 Fetching tokens without websites...")
tokens = supabase.table('token_discovery')\
    .select('id, contract_address, symbol, network')\
    .is_('website_url', 'null')\
    .limit(1000)\
    .execute()

print(f"✅ Found {len(tokens.data)} tokens to check")
print(f"⏱️ Estimated time: {len(tokens.data)/30:.1f} minutes")
print("")

total_checked = 0
websites_found = 0
start_time = time.time()

# Process in batches of 30
for i in range(0, len(tokens.data), 30):
    batch = tokens.data[i:i+30]
    addresses = [t['contract_address'] for t in batch]
    
    # Check with DexScreener
    data = check_token_batch(addresses)
    
    if data and 'pairs' in data:
        for token in batch:
            # Find matching pairs
            pairs = [p for p in data['pairs'] 
                    if p.get('baseToken', {}).get('address', '').lower() == token['contract_address'].lower()]
            
            update_data = {'website_checked_at': datetime.now().isoformat()}
            found_website = False
            
            for pair in pairs:
                info = pair.get('info', {})
                
                # Extract website
                websites = info.get('websites', [])
                if websites:
                    update_data['website_url'] = websites[0]['url']
                    found_website = True
                    websites_found += 1
                    print(f"  ✅ {token['symbol']}: {websites[0]['url']}")
                
                # Extract socials
                for social in info.get('socials', []):
                    if social['type'] == 'twitter':
                        update_data['twitter_url'] = social['url']
                    elif social['type'] == 'telegram':
                        update_data['telegram_url'] = social['url']
                    elif social['type'] == 'discord':
                        update_data['discord_url'] = social['url']
                
                if found_website:
                    break
            
            # Update database
            supabase.table('token_discovery').update(update_data).eq('id', token['id']).execute()
            total_checked += 1
    
    # Progress
    elapsed = time.time() - start_time
    rate = total_checked / elapsed if elapsed > 0 else 0
    print(f"Batch {i//30 + 1}/{(len(tokens.data)+29)//30}: "
          f"Checked {total_checked} | Websites: {websites_found} | "
          f"Rate: {rate:.1f}/s")
    
    time.sleep(0.5)  # Rate limiting

# Summary
print("\n" + "="*60)
print(f"✅ Checked {total_checked} tokens in {(time.time()-start_time)/60:.1f} minutes")
print(f"🌐 Found {websites_found} websites")
print(f"📊 Success rate: {websites_found/total_checked*100:.1f}%")