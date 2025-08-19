#!/usr/bin/env python3
"""
Batch check all tokens in token_discovery table for websites
Processes in batches of 30 (DexScreener API limit)
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
        else:
            print(f"API error: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error checking batch: {e}")
        return None

def process_tokens():
    """Process all tokens without websites"""
    
    # Get count of tokens to process
    count_result = supabase.table('token_discovery').select('*', count='exact').is_('website_url', 'null').execute()
    total_to_check = count_result.count
    print(f"🔍 Total tokens to check: {total_to_check}")
    
    # Get all tokens without websites
    print("📥 Fetching all tokens without websites...")
    all_tokens = []
    offset = 0
    batch_size = 1000
    
    while True:
        result = supabase.table('token_discovery')\
            .select('id, contract_address, symbol, network')\
            .is_('website_url', 'null')\
            .range(offset, offset + batch_size - 1)\
            .execute()
        
        if not result.data:
            break
            
        all_tokens.extend(result.data)
        offset += batch_size
        print(f"  Fetched {len(all_tokens)} tokens...")
        
        if len(result.data) < batch_size:
            break
    
    print(f"✅ Fetched {len(all_tokens)} tokens to check")
    
    # Process in batches of 30
    total_checked = 0
    websites_found = 0
    social_found = 0
    api_calls = 0
    start_time = time.time()
    
    for i in range(0, len(all_tokens), 30):
        batch = all_tokens[i:i+30]
        addresses = [t['contract_address'] for t in batch]
        
        # Check with DexScreener
        data = check_token_batch(addresses)
        api_calls += 1
        
        if not data:
            print(f"⚠️ Batch {i//30 + 1}: API failed, skipping")
            time.sleep(1)  # Wait before next batch
            continue
        
        # Process results
        batch_websites = 0
        batch_socials = 0
        
        for token in batch:
            # Find matching pairs for this token
            pairs = []
            if 'pairs' in data:
                pairs = [p for p in data['pairs'] 
                        if p.get('baseToken', {}).get('address', '').lower() == token['contract_address'].lower()]
            
            update_data = {'website_checked_at': datetime.now().isoformat()}
            found_something = False
            
            for pair in pairs:
                info = pair.get('info', {})
                if not info:
                    continue
                
                # Extract website
                websites = info.get('websites', [])
                if websites and 'website_url' not in update_data:
                    update_data['website_url'] = websites[0]['url']
                    batch_websites += 1
                    found_something = True
                
                # Extract social links
                socials = info.get('socials', [])
                for social in socials:
                    social_type = social.get('type')
                    social_url = social.get('url')
                    
                    if social_type == 'twitter' and 'twitter_url' not in update_data:
                        update_data['twitter_url'] = social_url
                        found_something = True
                    elif social_type == 'telegram' and 'telegram_url' not in update_data:
                        update_data['telegram_url'] = social_url
                        found_something = True
                    elif social_type == 'discord' and 'discord_url' not in update_data:
                        update_data['discord_url'] = social_url
                        found_something = True
                
                if found_something:
                    batch_socials += 1
                    break  # Found data, no need to check other pairs
            
            # Update database
            try:
                supabase.table('token_discovery').update(update_data).eq('id', token['id']).execute()
                total_checked += 1
            except Exception as e:
                print(f"Error updating token {token['symbol']}: {e}")
        
        websites_found += batch_websites
        social_found += batch_socials
        
        # Progress update
        elapsed = time.time() - start_time
        rate = total_checked / elapsed if elapsed > 0 else 0
        eta = (len(all_tokens) - total_checked) / rate if rate > 0 else 0
        
        print(f"Batch {i//30 + 1}/{(len(all_tokens)+29)//30}: "
              f"Checked {total_checked}/{len(all_tokens)} | "
              f"Websites: {websites_found} | "
              f"Socials: {social_found} | "
              f"Rate: {rate:.1f}/s | "
              f"ETA: {eta/60:.1f} min")
        
        # Rate limiting - DexScreener allows ~300 requests per minute
        # We're being conservative with 1 request per second
        time.sleep(1)
    
    # Final summary
    elapsed_total = time.time() - start_time
    print("\n" + "="*60)
    print("✅ BATCH PROCESSING COMPLETE")
    print(f"Total tokens checked: {total_checked}")
    print(f"Websites found: {websites_found}")
    print(f"Tokens with social links: {social_found}")
    print(f"API calls made: {api_calls}")
    print(f"Time taken: {elapsed_total/60:.1f} minutes")
    print(f"Average rate: {total_checked/elapsed_total:.1f} tokens/second")
    
    # Get final counts from database
    final_websites = supabase.table('token_discovery').select('*', count='exact').not_.is_('website_url', 'null').execute()
    final_twitter = supabase.table('token_discovery').select('*', count='exact').not_.is_('twitter_url', 'null').execute()
    final_telegram = supabase.table('token_discovery').select('*', count='exact').not_.is_('telegram_url', 'null').execute()
    
    print("\n📊 FINAL DATABASE STATS:")
    print(f"Total tokens with websites: {final_websites.count}")
    print(f"Total tokens with Twitter: {final_twitter.count}")
    print(f"Total tokens with Telegram: {final_telegram.count}")

if __name__ == "__main__":
    print("🚀 Starting batch website checker for all tokens")
    print(f"Time: {datetime.now().isoformat()}")
    print("="*60)
    
    try:
        process_tokens()
    except KeyboardInterrupt:
        print("\n⚠️ Process interrupted by user")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()