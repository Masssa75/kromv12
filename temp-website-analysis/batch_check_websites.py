#!/usr/bin/env python3
"""
Batch process all tokens to find websites using DexScreener API
Processes 30 tokens at a time for efficiency
"""

import os
import requests
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

def fetch_token_batch(contract_addresses):
    """Fetch data for multiple tokens from DexScreener"""
    try:
        # DexScreener batch endpoint - up to 30 addresses
        addresses_str = ','.join(contract_addresses)
        url = f"https://api.dexscreener.com/latest/dex/tokens/{addresses_str}"
        
        response = requests.get(url, headers={
            'Accept': 'application/json',
            'User-Agent': 'KROM Token Discovery Bot'
        })
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error fetching batch: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error in batch fetch: {e}")
        return None

def extract_social_data(token_data):
    """Extract website and social URLs from token data"""
    pairs = token_data.get('pairs', [])
    
    # Look for social data in any pair
    for pair in pairs:
        info = pair.get('info', {})
        if info:
            websites = info.get('websites', [])
            socials = info.get('socials', [])
            
            website_url = websites[0].get('url') if websites else None
            twitter_url = None
            telegram_url = None
            discord_url = None
            
            for social in socials:
                if social.get('type') == 'twitter':
                    twitter_url = social.get('url')
                elif social.get('type') == 'telegram':
                    telegram_url = social.get('url')
                elif social.get('type') == 'discord':
                    discord_url = social.get('url')
            
            has_social = bool(website_url or twitter_url or telegram_url or discord_url)
            return {
                'website_url': website_url,
                'twitter_url': twitter_url,
                'telegram_url': telegram_url,
                'discord_url': discord_url
            }, has_social
    
    return {
        'website_url': None,
        'twitter_url': None,
        'telegram_url': None,
        'discord_url': None
    }, False

def update_token_social_data(token_id, social_data):
    """Update token with social data in database"""
    try:
        update_data = {
            'website_checked_at': datetime.now().isoformat(),
            **social_data
        }
        
        response = supabase.table('token_discovery').update(update_data).eq('id', token_id).execute()
        return True
    except Exception as e:
        print(f"Error updating token {token_id}: {e}")
        return False

def main():
    print("=" * 60)
    print("BATCH WEBSITE DISCOVERY")
    print("=" * 60)
    print(f"Started at: {datetime.now().isoformat()}")
    print()
    
    # Get all tokens that haven't been checked or need rechecking
    print("Fetching tokens from database...")
    response = supabase.table('token_discovery').select('id, contract_address, symbol, network').execute()
    all_tokens = response.data
    
    print(f"Total tokens in database: {len(all_tokens)}")
    
    # Process in batches of 30
    batch_size = 30
    total_batches = (len(all_tokens) + batch_size - 1) // batch_size
    
    stats = {
        'total_processed': 0,
        'with_website': 0,
        'with_twitter': 0,
        'with_telegram': 0,
        'with_discord': 0,
        'with_any_social': 0,
        'errors': 0
    }
    
    print(f"Processing in {total_batches} batches of {batch_size} tokens each")
    print("-" * 60)
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(all_tokens))
        batch = all_tokens[start_idx:end_idx]
        
        print(f"\nBatch {batch_num + 1}/{total_batches} ({len(batch)} tokens)")
        
        # Extract contract addresses
        addresses = [token['contract_address'] for token in batch]
        
        # Fetch from DexScreener
        batch_data = fetch_token_batch(addresses)
        
        if batch_data and 'pairs' in batch_data:
            # Process each token in the response
            for token in batch:
                contract_address = token['contract_address']
                
                # Find this token's data in the response
                token_pairs = [p for p in batch_data['pairs'] 
                             if p.get('baseToken', {}).get('address', '').lower() == contract_address.lower()]
                
                if token_pairs:
                    # Create a token data structure similar to individual API response
                    token_data = {'pairs': token_pairs}
                    social_data, has_social = extract_social_data(token_data)
                    
                    # Update stats
                    if social_data['website_url']:
                        stats['with_website'] += 1
                        print(f"  ✅ {token['symbol']}: Website found")
                    if social_data['twitter_url']:
                        stats['with_twitter'] += 1
                    if social_data['telegram_url']:
                        stats['with_telegram'] += 1
                    if social_data['discord_url']:
                        stats['with_discord'] += 1
                    if has_social:
                        stats['with_any_social'] += 1
                        
                    # Update database
                    if update_token_social_data(token['id'], social_data):
                        stats['total_processed'] += 1
                    else:
                        stats['errors'] += 1
                else:
                    # No data found for this token
                    # Still mark as checked
                    update_data = {
                        'website_checked_at': datetime.now().isoformat()
                    }
                    try:
                        supabase.table('token_discovery').update(update_data).eq('id', token['id']).execute()
                        stats['total_processed'] += 1
                    except:
                        stats['errors'] += 1
        else:
            print(f"  ⚠️ Failed to fetch batch data")
            stats['errors'] += len(batch)
        
        # Rate limit - DexScreener allows ~300 requests/minute
        # With batch of 30, we can do 10 batches/minute safely
        if batch_num < total_batches - 1:
            time.sleep(6)  # 6 seconds between batches = 10 batches/minute
        
        # Progress update every 10 batches
        if (batch_num + 1) % 10 == 0:
            print(f"\n📊 Progress: {stats['total_processed']}/{len(all_tokens)} tokens")
            print(f"   Found {stats['with_website']} websites, {stats['with_any_social']} with any social")
    
    # Final summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total tokens processed: {stats['total_processed']}")
    print(f"Tokens with websites: {stats['with_website']} ({stats['with_website']*100/len(all_tokens):.1f}%)")
    print(f"Tokens with Twitter: {stats['with_twitter']} ({stats['with_twitter']*100/len(all_tokens):.1f}%)")
    print(f"Tokens with Telegram: {stats['with_telegram']} ({stats['with_telegram']*100/len(all_tokens):.1f}%)")
    print(f"Tokens with Discord: {stats['with_discord']} ({stats['with_discord']*100/len(all_tokens):.1f}%)")
    print(f"Tokens with ANY social: {stats['with_any_social']} ({stats['with_any_social']*100/len(all_tokens):.1f}%)")
    print(f"Errors: {stats['errors']}")
    print(f"\nCompleted at: {datetime.now().isoformat()}")
    
    # Estimated time
    total_time = total_batches * 6 / 60
    print(f"Estimated processing time: {total_time:.1f} minutes")

if __name__ == "__main__":
    main()