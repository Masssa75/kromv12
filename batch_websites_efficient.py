#!/usr/bin/env python3
"""
Efficient batch website checker using DexScreener's batch API
Processes 30 tokens per API call for maximum efficiency
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
    """Check a batch of up to 30 tokens using DexScreener batch API"""
    try:
        # DexScreener batch API - up to 30 addresses per call
        address_list = ','.join(addresses[:30])  # Ensure max 30
        response = requests.get(
            f'https://api.dexscreener.com/latest/dex/tokens/{address_list}',
            headers={'Accept': 'application/json'},
            timeout=15
        )
        if response.status_code == 200:
            return response.json()
        else:
            print(f"  ⚠️ API returned {response.status_code}")
            return None
    except requests.exceptions.Timeout:
        print(f"  ⚠️ API timeout")
        return None
    except Exception as e:
        print(f"  ⚠️ API error: {e}")
        return None

def main():
    print("🚀 Efficient Batch Website Checker")
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)
    
    # Get total count first
    count_result = supabase.table('token_discovery')\
        .select('*', count='exact')\
        .is_('website_url', 'null')\
        .execute()
    
    total_without_websites = count_result.count
    print(f"📊 Total tokens without websites: {total_without_websites:,}")
    print(f"📦 Will process in {(total_without_websites + 29) // 30:,} batches (30 tokens each)")
    print(f"⏱️ Estimated time: {total_without_websites / 30 / 60:.1f} minutes (at 1 batch/second)")
    print("")
    
    # Process in chunks to avoid memory issues
    chunk_size = 300  # Process 300 at a time (10 API calls)
    offset = 0
    
    total_checked = 0
    total_websites = 0
    total_twitter = 0
    total_telegram = 0
    total_discord = 0
    api_calls = 0
    start_time = time.time()
    
    while offset < total_without_websites:
        # Fetch next chunk
        print(f"\n📥 Fetching tokens {offset+1}-{min(offset+chunk_size, total_without_websites)}...")
        
        result = supabase.table('token_discovery')\
            .select('id, contract_address, symbol, network')\
            .is_('website_url', 'null')\
            .range(offset, offset + chunk_size - 1)\
            .execute()
        
        if not result.data:
            print("  No more tokens to process")
            break
        
        chunk_tokens = result.data
        print(f"  Processing {len(chunk_tokens)} tokens...")
        
        # Process this chunk in batches of 30
        for i in range(0, len(chunk_tokens), 30):
            batch = chunk_tokens[i:i+30]
            addresses = [t['contract_address'] for t in batch]
            
            # Call DexScreener batch API
            api_data = check_token_batch(addresses)
            api_calls += 1
            
            if api_data and 'pairs' in api_data:
                # Process each token in the batch
                for token in batch:
                    # Find pairs for this token
                    token_pairs = [
                        p for p in api_data['pairs']
                        if p.get('baseToken', {}).get('address', '').lower() == token['contract_address'].lower()
                    ]
                    
                    # Prepare update data
                    update_data = {'website_checked_at': datetime.now().isoformat()}
                    
                    # Extract info from first matching pair with info
                    for pair in token_pairs:
                        info = pair.get('info', {})
                        if not info:
                            continue
                        
                        # Get website
                        websites = info.get('websites', [])
                        if websites and 'website_url' not in update_data:
                            update_data['website_url'] = websites[0].get('url')
                            total_websites += 1
                            print(f"    ✅ {token['symbol']}: Found website!")
                        
                        # Get social links
                        socials = info.get('socials', [])
                        for social in socials:
                            social_type = social.get('type')
                            social_url = social.get('url')
                            
                            if social_type == 'twitter' and 'twitter_url' not in update_data:
                                update_data['twitter_url'] = social_url
                                total_twitter += 1
                            elif social_type == 'telegram' and 'telegram_url' not in update_data:
                                update_data['telegram_url'] = social_url
                                total_telegram += 1
                            elif social_type == 'discord' and 'discord_url' not in update_data:
                                update_data['discord_url'] = social_url
                                total_discord += 1
                        
                        # If we found any info, stop checking other pairs
                        if len(update_data) > 1:
                            break
                    
                    # Update database
                    try:
                        supabase.table('token_discovery')\
                            .update(update_data)\
                            .eq('id', token['id'])\
                            .execute()
                        total_checked += 1
                    except Exception as e:
                        print(f"    ❌ Error updating {token['symbol']}: {e}")
            
            # Progress update every 10 batches
            if (api_calls % 10) == 0:
                elapsed = time.time() - start_time
                rate = total_checked / elapsed if elapsed > 0 else 0
                eta = (total_without_websites - total_checked) / rate if rate > 0 else 0
                
                print(f"\n📈 Progress: {total_checked:,}/{total_without_websites:,} "
                      f"({total_checked/total_without_websites*100:.1f}%)")
                print(f"   Websites: {total_websites} | Twitter: {total_twitter} | "
                      f"Telegram: {total_telegram} | Discord: {total_discord}")
                print(f"   Speed: {rate:.1f} tokens/sec | ETA: {eta/60:.1f} min | "
                      f"API calls: {api_calls}")
            
            # Rate limiting - be nice to DexScreener
            time.sleep(0.5)  # 2 requests per second
        
        offset += chunk_size
    
    # Final summary
    elapsed_total = time.time() - start_time
    print("\n" + "="*70)
    print("✅ BATCH PROCESSING COMPLETE")
    print(f"⏰ Finished at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"⏱️ Total time: {elapsed_total/60:.1f} minutes")
    print("")
    print(f"📊 Results:")
    print(f"   Tokens checked: {total_checked:,}")
    print(f"   Websites found: {total_websites}")
    print(f"   Twitter links: {total_twitter}")
    print(f"   Telegram links: {total_telegram}")
    print(f"   Discord links: {total_discord}")
    print(f"   API calls made: {api_calls}")
    print(f"   Average speed: {total_checked/elapsed_total:.1f} tokens/second")
    
    # Get final database stats
    print("\n📊 Final Database Stats:")
    websites = supabase.table('token_discovery').select('*', count='exact').not_.is_('website_url', 'null').execute()
    twitter = supabase.table('token_discovery').select('*', count='exact').not_.is_('twitter_url', 'null').execute()
    telegram = supabase.table('token_discovery').select('*', count='exact').not_.is_('telegram_url', 'null').execute()
    discord = supabase.table('token_discovery').select('*', count='exact').not_.is_('discord_url', 'null').execute()
    
    print(f"   Total tokens with websites: {websites.count}")
    print(f"   Total tokens with Twitter: {twitter.count}")
    print(f"   Total tokens with Telegram: {telegram.count}")
    print(f"   Total tokens with Discord: {discord.count}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️ Process interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()