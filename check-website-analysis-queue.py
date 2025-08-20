#!/usr/bin/env python3
"""
Check which tokens are ready for website analysis
"""

import os
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

def check_analysis_queue():
    """Check tokens ready for website analysis"""
    
    print("\n🔍 Checking website analysis status...")
    
    # Count tokens with website_url
    response = supabase.table('crypto_calls') \
        .select('id', count='exact') \
        .not_.is_('website_url', 'null') \
        .execute()
    
    with_website = response.count
    print(f"\n📊 Tokens WITH website_url: {with_website}")
    
    # Count tokens with website_url but no website_score (need analysis)
    response = supabase.table('crypto_calls') \
        .select('id', count='exact') \
        .not_.is_('website_url', 'null') \
        .is_('website_score', 'null') \
        .execute()
    
    need_analysis = response.count
    print(f"⏳ Tokens needing website analysis: {need_analysis}")
    
    # Count tokens with website_url AND website_score (already analyzed)
    response = supabase.table('crypto_calls') \
        .select('id', count='exact') \
        .not_.is_('website_url', 'null') \
        .not_.is_('website_score', 'null') \
        .execute()
    
    already_analyzed = response.count
    print(f"✅ Tokens already analyzed: {already_analyzed}")
    
    # Get examples of tokens needing analysis
    if need_analysis > 0:
        response = supabase.table('crypto_calls') \
            .select('ticker, website_url, created_at') \
            .not_.is_('website_url', 'null') \
            .is_('website_score', 'null') \
            .order('created_at', desc=True) \
            .limit(10) \
            .execute()
        
        print(f"\n📋 Next tokens for analysis (newest first):")
        for token in response.data:
            ticker = token['ticker'][:10]
            url = token['website_url'][:50] if len(token['website_url']) > 50 else token['website_url']
            created = token['created_at'][:19]
            print(f"  {ticker:<10} {url:<50} Created: {created}")
    
    # Check for failed analyses (score = 0)
    response = supabase.table('crypto_calls') \
        .select('id', count='exact') \
        .eq('website_score', 0) \
        .execute()
    
    failed_count = response.count
    if failed_count > 0:
        print(f"\n⚠️  Failed analyses (score=0): {failed_count}")
    
    # Check distribution of analyzed scores
    print(f"\n📊 Website score distribution (for analyzed tokens):")
    
    # Get score ranges
    response = supabase.table('crypto_calls') \
        .select('website_score, website_tier') \
        .not_.is_('website_score', 'null') \
        .execute()
    
    if response.data:
        tiers = {}
        score_ranges = {
            'FAILED (0)': 0,
            'Low (1-7)': 0,
            'Medium (8-14)': 0,
            'High (15-21)': 0
        }
        
        for token in response.data:
            score = token['website_score']
            tier = token.get('website_tier', 'UNKNOWN')
            
            # Count by tier
            tiers[tier] = tiers.get(tier, 0) + 1
            
            # Count by score range
            if score == 0:
                score_ranges['FAILED (0)'] += 1
            elif 1 <= score <= 7:
                score_ranges['Low (1-7)'] += 1
            elif 8 <= score <= 14:
                score_ranges['Medium (8-14)'] += 1
            elif 15 <= score <= 21:
                score_ranges['High (15-21)'] += 1
        
        print("  By score range:")
        for range_name, count in score_ranges.items():
            print(f"    {range_name}: {count}")
        
        print("\n  By tier:")
        for tier, count in sorted(tiers.items()):
            print(f"    {tier}: {count}")

def main():
    check_analysis_queue()
    
    print("\n" + "="*60)
    print("📝 SUMMARY:")
    print("The batch analyzer looks for: website_url NOT NULL AND website_score IS NULL")
    print("If no tokens match this criteria, the batch analyzer has nothing to do")
    print("="*60)

if __name__ == "__main__":
    main()