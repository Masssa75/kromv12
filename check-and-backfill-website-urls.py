#!/usr/bin/env python3
"""
Check for website URLs in raw_data and backfill the website_url column
"""

import os
import json
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("❌ Missing Supabase credentials in .env file")
    exit(1)

# Create Supabase client with service role key (needed for RLS)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def check_website_urls():
    """Check how many tokens have website URLs in different places"""
    print("\n🔍 Checking website URL status in database...")
    
    # Check tokens with website_url populated
    response = supabase.table('crypto_calls') \
        .select('id', count='exact') \
        .not_.is_('website_url', 'null') \
        .execute()
    
    with_website_url = response.count
    print(f"✅ Tokens with website_url column populated: {with_website_url}")
    
    # Check tokens with twitter_url populated
    response = supabase.table('crypto_calls') \
        .select('id', count='exact') \
        .not_.is_('twitter_url', 'null') \
        .execute()
    
    with_twitter = response.count
    print(f"🐦 Tokens with twitter_url column populated: {with_twitter}")
    
    # Get a sample of tokens to check raw_data
    response = supabase.table('crypto_calls') \
        .select('id, ticker, raw_data, website_url, twitter_url, telegram_url, discord_url') \
        .limit(100) \
        .execute()
    
    tokens_with_raw_website = 0
    tokens_with_raw_twitter = 0
    tokens_needing_backfill = []
    
    for token in response.data:
        raw_data = token.get('raw_data')
        if raw_data:
            # Check for website in raw_data
            raw_website = raw_data.get('token', {}).get('websiteUrl')
            raw_twitter = raw_data.get('token', {}).get('twitterUrl')
            raw_telegram = raw_data.get('token', {}).get('telegramUrl')
            
            if raw_website:
                tokens_with_raw_website += 1
                if not token.get('website_url'):
                    tokens_needing_backfill.append({
                        'id': token['id'],
                        'ticker': token['ticker'],
                        'website': raw_website,
                        'twitter': raw_twitter,
                        'telegram': raw_telegram
                    })
            
            if raw_twitter:
                tokens_with_raw_twitter += 1
    
    print(f"\n📊 Sample Analysis (100 tokens):")
    print(f"  - Tokens with website in raw_data: {tokens_with_raw_website}")
    print(f"  - Tokens with twitter in raw_data: {tokens_with_raw_twitter}")
    print(f"  - Tokens needing backfill: {len(tokens_needing_backfill)}")
    
    if tokens_needing_backfill:
        print(f"\n🔧 Example tokens that need backfill:")
        for token in tokens_needing_backfill[:5]:
            print(f"  - {token['ticker']}: {token['website']}")
    
    return tokens_needing_backfill

def backfill_website_urls(limit=None):
    """Backfill website URLs from raw_data to dedicated columns"""
    print("\n🔄 Starting backfill process...")
    
    # Get all tokens with raw_data but no website_url
    query = supabase.table('crypto_calls') \
        .select('id, ticker, raw_data') \
        .is_('website_url', 'null') \
        .not_.is_('raw_data', 'null')
    
    if limit:
        query = query.limit(limit)
    
    response = query.execute()
    tokens = response.data
    
    print(f"Found {len(tokens)} tokens to process")
    
    updated_count = 0
    error_count = 0
    
    for token in tokens:
        try:
            raw_data = token.get('raw_data')
            if not raw_data:
                continue
            
            # Extract URLs from raw_data
            token_data = raw_data.get('token', {})
            website_url = token_data.get('websiteUrl')
            twitter_url = token_data.get('twitterUrl')
            telegram_url = token_data.get('telegramUrl')
            discord_url = token_data.get('discordUrl')
            
            # Only update if we found at least one URL
            if website_url or twitter_url or telegram_url or discord_url:
                update_data = {}
                if website_url:
                    update_data['website_url'] = website_url
                if twitter_url:
                    update_data['twitter_url'] = twitter_url
                if telegram_url:
                    update_data['telegram_url'] = telegram_url
                if discord_url:
                    update_data['discord_url'] = discord_url
                
                # Add timestamp for tracking
                update_data['socials_fetched_at'] = 'now()'
                
                # Update the token
                response = supabase.table('crypto_calls') \
                    .update(update_data) \
                    .eq('id', token['id']) \
                    .execute()
                
                updated_count += 1
                urls_found = []
                if website_url:
                    urls_found.append('Web')
                if twitter_url:
                    urls_found.append('Twitter')
                if telegram_url:
                    urls_found.append('Telegram')
                if discord_url:
                    urls_found.append('Discord')
                    
                print(f"  ✅ Updated {token['ticker']}: {', '.join(urls_found)}")
                
        except Exception as e:
            error_count += 1
            print(f"  ❌ Error updating {token['ticker']}: {str(e)}")
    
    print(f"\n📊 Backfill Results:")
    print(f"  - Successfully updated: {updated_count}")
    print(f"  - Errors: {error_count}")
    print(f"  - Skipped (no URLs found): {len(tokens) - updated_count - error_count}")
    
    return updated_count

def investigate_deeper():
    """Do a deeper investigation of where website URLs might be"""
    print("\n🔬 Deep investigation of website URL sources...")
    
    # Get a larger sample to analyze
    response = supabase.table('crypto_calls') \
        .select('id, ticker, raw_data, website_url, twitter_url, created_at') \
        .order('created_at', desc=True) \
        .limit(500) \
        .execute()
    
    stats = {
        'total': len(response.data),
        'has_website_url_column': 0,
        'has_twitter_url_column': 0,
        'has_raw_data': 0,
        'has_website_in_raw': 0,
        'has_twitter_in_raw': 0,
        'missing_website_but_in_raw': 0,
        'no_website_anywhere': 0
    }
    
    examples_missing_website = []
    examples_with_website = []
    
    for token in response.data:
        # Check column values
        if token.get('website_url'):
            stats['has_website_url_column'] += 1
            examples_with_website.append({
                'ticker': token['ticker'],
                'website': token['website_url'],
                'created': token['created_at']
            })
        
        if token.get('twitter_url'):
            stats['has_twitter_url_column'] += 1
        
        # Check raw_data
        raw_data = token.get('raw_data')
        if raw_data:
            stats['has_raw_data'] += 1
            
            # Check for URLs in raw_data.token
            token_data = raw_data.get('token', {})
            if token_data.get('websiteUrl'):
                stats['has_website_in_raw'] += 1
                
                # Check if it's missing from column but present in raw
                if not token.get('website_url'):
                    stats['missing_website_but_in_raw'] += 1
                    examples_missing_website.append({
                        'ticker': token['ticker'],
                        'raw_website': token_data.get('websiteUrl'),
                        'created': token['created_at']
                    })
            
            if token_data.get('twitterUrl'):
                stats['has_twitter_in_raw'] += 1
        
        # Count tokens with no website anywhere
        has_website_somewhere = (
            token.get('website_url') or 
            (raw_data and raw_data.get('token', {}).get('websiteUrl'))
        )
        if not has_website_somewhere:
            stats['no_website_anywhere'] += 1
    
    print(f"\n📊 Analysis of {stats['total']} most recent tokens:")
    print(f"  Website URL in column: {stats['has_website_url_column']} ({stats['has_website_url_column']/stats['total']*100:.1f}%)")
    print(f"  Twitter URL in column: {stats['has_twitter_url_column']} ({stats['has_twitter_url_column']/stats['total']*100:.1f}%)")
    print(f"  Has raw_data: {stats['has_raw_data']} ({stats['has_raw_data']/stats['total']*100:.1f}%)")
    print(f"  Website in raw_data: {stats['has_website_in_raw']} ({stats['has_website_in_raw']/stats['total']*100:.1f}%)")
    print(f"  Twitter in raw_data: {stats['has_twitter_in_raw']} ({stats['has_twitter_in_raw']/stats['total']*100:.1f}%)")
    
    print(f"\n⚠️  Missing website_url but exists in raw_data: {stats['missing_website_but_in_raw']}")
    print(f"❌ No website anywhere: {stats['no_website_anywhere']} ({stats['no_website_anywhere']/stats['total']*100:.1f}%)")
    
    if examples_with_website:
        print(f"\n✅ Examples WITH website_url populated (first 3):")
        for ex in examples_with_website[:3]:
            print(f"  - {ex['ticker']}: {ex['website']} (created: {ex['created']})")
    
    if examples_missing_website:
        print(f"\n⚠️  Examples MISSING website_url but have it in raw_data (first 5):")
        for ex in examples_missing_website[:5]:
            print(f"  - {ex['ticker']}: {ex['raw_website']} (created: {ex['created']})")
    
    return stats

def main():
    # First, check the current state
    check_website_urls()
    
    # Do deeper investigation
    investigate_deeper()
    
    print("\n" + "="*50)
    print("\n📝 INVESTIGATION COMPLETE - No changes made to database")
    print("\nKey findings will help determine next steps for fixing the website URL storage issue.")

if __name__ == "__main__":
    main()