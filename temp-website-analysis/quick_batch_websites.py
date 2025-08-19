#!/usr/bin/env python3
"""
Quick batch processor - updates database with website data
"""

import os
import requests
import time
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

print("Quick Batch Website Processor")
print("=" * 60)

# Get all tokens without website check
response = supabase.table('token_discovery').select('id, contract_address, symbol').is_('website_checked_at', 'null').limit(300).execute()
tokens = response.data

print(f"Found {len(tokens)} unchecked tokens")

# Process in batches of 30
batch_size = 30
total_websites = 0

for i in range(0, len(tokens), batch_size):
    batch = tokens[i:i+batch_size]
    print(f"\nBatch {i//batch_size + 1}: Processing {len(batch)} tokens...")
    
    # Create comma-separated addresses
    addresses = ','.join([t['contract_address'] for t in batch])
    
    # Fetch from DexScreener
    try:
        response = requests.get(
            f"https://api.dexscreener.com/latest/dex/tokens/{addresses}",
            headers={'Accept': 'application/json'}
        )
        data = response.json()
        
        # Process each token
        for token in batch:
            # Find matching pairs
            matching_pairs = [
                p for p in data.get('pairs', [])
                if p.get('baseToken', {}).get('address', '').lower() == token['contract_address'].lower()
            ]
            
            # Extract social data
            update_data = {'website_checked_at': datetime.now().isoformat()}
            
            for pair in matching_pairs:
                info = pair.get('info', {})
                if info:
                    websites = info.get('websites', [])
                    if websites and not update_data.get('website_url'):
                        update_data['website_url'] = websites[0].get('url')
                        total_websites += 1
                        print(f"  ✅ {token['symbol']}: Website found")
                    
                    socials = info.get('socials', [])
                    for social in socials:
                        if social.get('type') == 'twitter' and not update_data.get('twitter_url'):
                            update_data['twitter_url'] = social.get('url')
                        elif social.get('type') == 'telegram' and not update_data.get('telegram_url'):
                            update_data['telegram_url'] = social.get('url')
                        elif social.get('type') == 'discord' and not update_data.get('discord_url'):
                            update_data['discord_url'] = social.get('url')
                    break  # Use first pair with info
            
            # Update database
            supabase.table('token_discovery').update(update_data).eq('id', token['id']).execute()
            
    except Exception as e:
        print(f"  Error: {e}")
    
    # Rate limit
    time.sleep(2)

print(f"\n{'=' * 60}")
print(f"Completed! Found {total_websites} websites")
print("Refresh your dashboard to see updated data")