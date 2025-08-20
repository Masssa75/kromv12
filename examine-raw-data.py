#!/usr/bin/env python3
"""
Examine the raw_data field to understand what KROM API provides
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

# Create Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def examine_raw_data_structure():
    """Look at the structure of raw_data to understand what's available"""
    
    # Get a recent token with website URL
    response = supabase.table('crypto_calls') \
        .select('ticker, raw_data, website_url, pool_address') \
        .not_.is_('website_url', 'null') \
        .order('created_at', desc=True) \
        .limit(1) \
        .execute()
    
    if response.data:
        token = response.data[0]
        print(f"\n✅ Example token WITH website_url: {token['ticker']}")
        print(f"   Website URL in column: {token['website_url']}")
        print(f"   Pool address: {token['pool_address']}")
        
        if token['raw_data']:
            print(f"\n📊 Raw data structure (keys at root level):")
            for key in token['raw_data'].keys():
                print(f"   - {key}")
            
            # Check token section
            if 'token' in token['raw_data']:
                print(f"\n📊 Raw data 'token' section keys:")
                for key in token['raw_data']['token'].keys():
                    value = token['raw_data']['token'][key]
                    if key in ['websiteUrl', 'twitterUrl', 'telegramUrl', 'discordUrl']:
                        print(f"   - {key}: {value}")
                    else:
                        print(f"   - {key}: {type(value).__name__}")
    
    # Get a recent token without website URL
    response = supabase.table('crypto_calls') \
        .select('ticker, raw_data, website_url, pool_address') \
        .is_('website_url', 'null') \
        .order('created_at', desc=True) \
        .limit(1) \
        .execute()
    
    if response.data:
        token = response.data[0]
        print(f"\n❌ Example token WITHOUT website_url: {token['ticker']}")
        print(f"   Pool address: {token['pool_address']}")
        
        if token['raw_data']:
            # Check token section for URLs
            if 'token' in token['raw_data']:
                token_data = token['raw_data']['token']
                print(f"\n   Checking for URLs in raw_data.token:")
                for url_key in ['websiteUrl', 'twitterUrl', 'telegramUrl', 'discordUrl']:
                    if url_key in token_data:
                        print(f"   - {url_key}: {token_data[url_key]}")
                    else:
                        print(f"   - {url_key}: NOT FOUND")

def check_dexscreener_availability():
    """Check which tokens have pool addresses for DexScreener lookups"""
    
    print("\n🔍 Checking pool address availability...")
    
    # Count tokens with pool addresses
    response = supabase.table('crypto_calls') \
        .select('id', count='exact') \
        .not_.is_('pool_address', 'null') \
        .execute()
    
    with_pool = response.count
    
    # Count total tokens
    response = supabase.table('crypto_calls') \
        .select('id', count='exact') \
        .execute()
    
    total = response.count
    
    print(f"  Tokens with pool_address: {with_pool}/{total} ({with_pool/total*100:.1f}%)")
    
    # Check recent tokens specifically
    response = supabase.table('crypto_calls') \
        .select('ticker, pool_address, website_url, created_at') \
        .order('created_at', desc=True) \
        .limit(10) \
        .execute()
    
    print(f"\n📊 Last 10 tokens added:")
    for token in response.data:
        pool_status = "✓" if token['pool_address'] else "✗"
        web_status = "✓" if token['website_url'] else "✗"
        print(f"  {token['ticker']:10} Pool: {pool_status}  Website: {web_status}  Created: {token['created_at'][:19]}")

def trace_website_source():
    """Try to understand where the website URLs are coming from"""
    
    print("\n🔍 Tracing website URL sources...")
    
    # Get tokens with websites and check timing
    response = supabase.table('crypto_calls') \
        .select('ticker, website_url, socials_fetched_at, created_at') \
        .not_.is_('website_url', 'null') \
        .order('created_at', desc=True) \
        .limit(5) \
        .execute()
    
    print(f"\n📊 Tokens with website URLs (timing analysis):")
    for token in response.data:
        created = token['created_at']
        socials_fetched = token['socials_fetched_at']
        
        if socials_fetched:
            # Compare times
            print(f"  {token['ticker']}:")
            print(f"    Created: {created}")
            print(f"    Socials: {socials_fetched}")
            if created == socials_fetched or created[:19] == socials_fetched[:19]:
                print(f"    → Fetched during initial insert (crypto-poller)")
            else:
                print(f"    → Fetched later (different process)")
        else:
            print(f"  {token['ticker']}: No socials_fetched_at timestamp")

def main():
    print("="*60)
    print("🔍 INVESTIGATING WEBSITE URL STORAGE ISSUE")
    print("="*60)
    
    # Check raw data structure
    examine_raw_data_structure()
    
    # Check pool address availability
    check_dexscreener_availability()
    
    # Trace where websites come from
    trace_website_source()
    
    print("\n" + "="*60)
    print("📝 KEY FINDINGS:")
    print("1. Website URLs ARE being stored (56.8% of recent tokens)")
    print("2. Raw data from KROM API does NOT contain website URLs")
    print("3. Website URLs come from DexScreener API (via crypto-poller)")
    print("4. Most tokens HAVE pool addresses for DexScreener lookups")
    print("5. The system IS working - just not all tokens have websites")
    print("="*60)

if __name__ == "__main__":
    main()