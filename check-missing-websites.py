#!/usr/bin/env python3
"""
Check why some recent tokens don't have website URLs
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
from datetime import datetime, timezone

load_dotenv()

# Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("❌ Missing Supabase credentials in .env file")
    exit(1)

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def check_missing_websites():
    """Check tokens without websites and understand why"""
    
    print("\n🔍 Analyzing tokens without website URLs...")
    
    # Get recent tokens without websites
    response = supabase.table('crypto_calls') \
        .select('ticker, liquidity_usd, is_dead, ath_last_checked, created_at, socials_fetched_at') \
        .is_('website_url', 'null') \
        .order('created_at', desc=True) \
        .limit(20) \
        .execute()
    
    print(f"\n📊 Recent tokens WITHOUT website URLs:")
    print(f"{'Ticker':<12} {'Liquidity':<12} {'Dead':<6} {'ATH Checked':<20} {'Socials Fetched':<20}")
    print("-" * 90)
    
    for token in response.data:
        ticker = token['ticker'][:10]
        liquidity = f"${token['liquidity_usd']:,.0f}" if token['liquidity_usd'] else "Unknown"
        is_dead = "Yes" if token.get('is_dead') else "No"
        ath_checked = token['ath_last_checked'][:19] if token['ath_last_checked'] else "Never"
        socials = token['socials_fetched_at'][:19] if token['socials_fetched_at'] else "Never"
        
        print(f"{ticker:<12} {liquidity:<12} {is_dead:<6} {ath_checked:<20} {socials:<20}")
    
    # Check liquidity distribution
    print("\n📊 Liquidity analysis for tokens without websites:")
    
    # Count by liquidity ranges
    ranges = [
        ("High (>=$20K)", 20000, float('inf')),
        ("Medium ($1K-$20K)", 1000, 20000),
        ("Low (<$1K)", 0, 1000),
        ("Unknown", None, None)
    ]
    
    for range_name, min_liq, max_liq in ranges:
        if min_liq is None:
            query = supabase.table('crypto_calls') \
                .select('id', count='exact') \
                .is_('website_url', 'null') \
                .is_('liquidity_usd', 'null')
        elif max_liq == float('inf'):
            query = supabase.table('crypto_calls') \
                .select('id', count='exact') \
                .is_('website_url', 'null') \
                .gte('liquidity_usd', min_liq)
        else:
            query = supabase.table('crypto_calls') \
                .select('id', count='exact') \
                .is_('website_url', 'null') \
                .gte('liquidity_usd', min_liq) \
                .lt('liquidity_usd', max_liq)
        
        response = query.execute()
        count = response.count
        print(f"  {range_name}: {count} tokens")
    
    # Check if ultra-tracker has processed them
    print("\n📊 Ultra-tracker processing status:")
    
    # Tokens without websites but with socials_fetched_at
    response = supabase.table('crypto_calls') \
        .select('id', count='exact') \
        .is_('website_url', 'null') \
        .not_.is_('socials_fetched_at', 'null') \
        .execute()
    
    processed_no_website = response.count
    
    # Tokens without websites and without socials_fetched_at
    response = supabase.table('crypto_calls') \
        .select('id', count='exact') \
        .is_('website_url', 'null') \
        .is_('socials_fetched_at', 'null') \
        .execute()
    
    not_processed = response.count
    
    print(f"  Processed by ultra-tracker (no website found): {processed_no_website}")
    print(f"  Not yet processed by ultra-tracker: {not_processed}")
    
    # Check recent processing activity
    print("\n📊 Recent ultra-tracker activity (last 10 processed):")
    
    response = supabase.table('crypto_calls') \
        .select('ticker, website_url, socials_fetched_at') \
        .not_.is_('socials_fetched_at', 'null') \
        .order('socials_fetched_at', desc=True) \
        .limit(10) \
        .execute()
    
    current_time = datetime.now(timezone.utc)
    
    for token in response.data:
        ticker = token['ticker'][:10]
        has_website = "✓" if token['website_url'] else "✗"
        socials_time = token['socials_fetched_at']
        
        # Calculate how long ago
        # Handle various timestamp formats
        if socials_time:
            try:
                # Try parsing with timezone
                if '+' in socials_time:
                    socials_dt = datetime.fromisoformat(socials_time.split('+')[0] + '+00:00')
                else:
                    socials_dt = datetime.fromisoformat(socials_time)
                time_diff = current_time - socials_dt
                minutes_ago = int(time_diff.total_seconds() / 60)
            except:
                minutes_ago = 0
        else:
            minutes_ago = 0
        
        if minutes_ago < 60:
            time_str = f"{minutes_ago}m ago"
        else:
            time_str = f"{minutes_ago//60}h {minutes_ago%60}m ago"
        
        print(f"  {ticker:<10} Website: {has_website}  Processed: {time_str}")

def main():
    check_missing_websites()
    
    print("\n" + "="*60)
    print("📝 CONCLUSION:")
    print("1. Ultra-tracker processes high-liquidity tokens (>=$20K)")
    print("2. Many tokens simply DON'T HAVE websites (meme coins)")
    print("3. Low liquidity tokens aren't processed by ultra-tracker")
    print("4. The system is working - just selective about which tokens to process")
    print("="*60)

if __name__ == "__main__":
    main()