#!/usr/bin/env python3
"""
Batch fetch and store social links (website, twitter, telegram) from DexScreener
This populates the database so the UI doesn't need to fetch on every modal open
"""

import os
import json
import requests
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Initialize Supabase
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_batch_from_dexscreener(addresses: List[str]) -> Dict[str, Any]:
    """
    Fetch multiple tokens from DexScreener in one API call
    DexScreener supports up to 30 addresses per request
    """
    try:
        # DexScreener expects lowercase addresses
        addresses_str = ','.join([addr.lower() for addr in addresses])
        url = f"https://api.dexscreener.com/latest/dex/tokens/{addresses_str}"
        
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        results = {}
        
        for pair_data in data.get('pairs', []):
            # Use contract address as key
            contract = pair_data.get('baseToken', {}).get('address', '').lower()
            if not contract:
                continue
            
            # Skip if we already have data for this contract (use highest liquidity pair)
            if contract in results:
                existing_liquidity = results[contract].get('liquidity_usd', 0)
                new_liquidity = pair_data.get('liquidity', {}).get('usd', 0)
                if new_liquidity <= existing_liquidity:
                    continue
            
            # Extract social links
            socials = pair_data.get('info', {}).get('socials', [])
            
            website_url = None
            twitter_url = None
            telegram_url = None
            discord_url = None
            
            for social in socials:
                social_type = social.get('type', '')
                social_url = social.get('url', '')
                
                if social_type == 'website' and not website_url:
                    website_url = social_url
                elif social_type == 'twitter' and not twitter_url:
                    twitter_url = social_url
                elif social_type == 'telegram' and not telegram_url:
                    telegram_url = social_url
                elif social_type == 'discord' and not discord_url:
                    discord_url = social_url
            
            # Also check for direct website in info
            if not website_url and pair_data.get('info', {}).get('websites'):
                websites = pair_data['info']['websites']
                if isinstance(websites, list) and len(websites) > 0:
                    website_url = websites[0].get('url') if isinstance(websites[0], dict) else websites[0]
            
            results[contract] = {
                'website_url': website_url,
                'twitter_url': twitter_url,
                'telegram_url': telegram_url,
                'discord_url': discord_url,
                'liquidity_usd': pair_data.get('liquidity', {}).get('usd', 0),
                'price_usd': pair_data.get('priceUsd'),
                'dex': pair_data.get('dexId'),
                'chain': pair_data.get('chainId')
            }
        
        return results
        
    except Exception as e:
        print(f"Error fetching batch: {e}")
        return {}

def update_socials_batch():
    """
    Fetch and update social links for all tokens missing this data
    """
    print("🔄 Starting batch social links update...")
    
    # Get tokens that don't have social links or haven't been updated in 7 days
    cutoff_date = datetime.now() - timedelta(days=7)
    
    result = supabase.table('crypto_calls').select(
        'id, contract_address, ticker, network, socials_fetched_at'
    ).or_(
        f'socials_fetched_at.is.null,socials_fetched_at.lt.{cutoff_date.isoformat()}'
    ).order('created_at', desc=True).execute()
    
    tokens = result.data
    print(f"Found {len(tokens)} tokens to update")
    
    if not tokens:
        print("No tokens need updating")
        return
    
    # Process in batches of 30 (DexScreener limit)
    batch_size = 30
    updated_count = 0
    failed_count = 0
    
    for i in range(0, len(tokens), batch_size):
        batch = tokens[i:i+batch_size]
        addresses = [t['contract_address'] for t in batch]
        
        print(f"\n📡 Fetching batch {i//batch_size + 1}/{(len(tokens)-1)//batch_size + 1} ({len(batch)} tokens)...")
        
        # Fetch from DexScreener
        results = fetch_batch_from_dexscreener(addresses)
        
        if not results:
            print(f"  ⚠️ No results from DexScreener")
            failed_count += len(batch)
            continue
        
        # Update database for each token
        for token in batch:
            contract_lower = token['contract_address'].lower()
            
            if contract_lower in results:
                data = results[contract_lower]
                
                # Prepare update
                update_data = {
                    'website_url': data['website_url'],
                    'twitter_url': data['twitter_url'],
                    'telegram_url': data['telegram_url'],
                    'discord_url': data['discord_url'],
                    'socials_fetched_at': datetime.now().isoformat()
                }
                
                # Remove None values to avoid overwriting existing data
                update_data = {k: v for k, v in update_data.items() if v is not None}
                
                # Always update the timestamp even if no socials found
                if 'website_url' not in update_data:
                    update_data['socials_fetched_at'] = datetime.now().isoformat()
                
                try:
                    supabase.table('crypto_calls').update(update_data).eq('id', token['id']).execute()
                    
                    if data['website_url']:
                        print(f"  ✅ {token['ticker']:8} - Website: {data['website_url'][:50]}...")
                    else:
                        print(f"  ⚠️ {token['ticker']:8} - No website found")
                    
                    updated_count += 1
                    
                except Exception as e:
                    print(f"  ❌ {token['ticker']:8} - Update failed: {e}")
                    failed_count += 1
            else:
                # Mark as checked even if not found on DexScreener
                try:
                    supabase.table('crypto_calls').update({
                        'socials_fetched_at': datetime.now().isoformat()
                    }).eq('id', token['id']).execute()
                    
                    print(f"  ⚠️ {token['ticker']:8} - Not found on DexScreener")
                    updated_count += 1
                    
                except Exception as e:
                    print(f"  ❌ {token['ticker']:8} - Update failed: {e}")
                    failed_count += 1
        
        # Rate limiting - be nice to DexScreener
        if i + batch_size < len(tokens):
            time.sleep(1)
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 BATCH UPDATE COMPLETE")
    print(f"{'='*60}")
    print(f"Total processed: {len(tokens)}")
    print(f"Successfully updated: {updated_count}")
    print(f"Failed: {failed_count}")
    
    # Check how many tokens now have websites
    result = supabase.table('crypto_calls').select(
        'count',
        count='exact'
    ).not_.is_('website_url', 'null').execute()
    
    website_count = result.count if result else 0
    
    result = supabase.table('crypto_calls').select(
        'count',
        count='exact'
    ).execute()
    
    total_count = result.count if result else 0
    
    print(f"\nTokens with websites: {website_count}/{total_count} ({website_count/total_count*100:.1f}%)")

def check_current_status():
    """
    Check current status of social links in database
    """
    print("\n📈 Current Database Status:")
    
    # Total tokens
    result = supabase.table('crypto_calls').select('count', count='exact').execute()
    total = result.count if result else 0
    print(f"Total tokens: {total}")
    
    # Tokens with website
    result = supabase.table('crypto_calls').select('count', count='exact').not_.is_('website_url', 'null').execute()
    with_website = result.count if result else 0
    print(f"With website: {with_website} ({with_website/total*100:.1f}%)")
    
    # Tokens with twitter
    result = supabase.table('crypto_calls').select('count', count='exact').not_.is_('twitter_url', 'null').execute()
    with_twitter = result.count if result else 0
    print(f"With Twitter: {with_twitter} ({with_twitter/total*100:.1f}%)")
    
    # Tokens with telegram
    result = supabase.table('crypto_calls').select('count', count='exact').not_.is_('telegram_url', 'null').execute()
    with_telegram = result.count if result else 0
    print(f"With Telegram: {with_telegram} ({with_telegram/total*100:.1f}%)")
    
    # Never fetched
    result = supabase.table('crypto_calls').select('count', count='exact').is_('socials_fetched_at', 'null').execute()
    never_fetched = result.count if result else 0
    print(f"Never fetched: {never_fetched} ({never_fetched/total*100:.1f}%)")

if __name__ == "__main__":
    print("🌐 Batch Social Links Fetcher")
    print("=" * 60)
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Error: Supabase credentials not found in .env")
        exit(1)
    
    # Check current status
    check_current_status()
    
    print("\n" + "=" * 60)
    
    # Run the batch update
    update_socials_batch()
    
    print("\n" + "=" * 60)
    
    # Check status after update
    check_current_status()