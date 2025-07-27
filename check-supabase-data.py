#!/usr/bin/env python3
"""Check Supabase database for crypto calls and analysis data"""

import os
from supabase import create_client, Client
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")

if not url or not key:
    print("ERROR: Missing Supabase credentials in .env file")
    print("Please ensure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set")
    exit(1)

supabase: Client = create_client(url, key)

print("Connecting to Supabase...")
print("=" * 60)

# Check if crypto_calls table exists and get stats
try:
    # Get total count
    total_result = supabase.table('crypto_calls').select('*', count='exact').execute()
    total_count = total_result.count if hasattr(total_result, 'count') else len(total_result.data)
    
    print(f"Total calls in Supabase: {total_count:,}")
    
    # Get calls from last 2 months
    two_months_ago = (datetime.now() - timedelta(days=60)).isoformat()
    recent_result = supabase.table('crypto_calls') \
        .select('*', count='exact') \
        .gte('created_at', two_months_ago) \
        .execute()
    recent_count = recent_result.count if hasattr(recent_result, 'count') else len(recent_result.data)
    
    print(f"Calls from last 2 months: {recent_count:,}")
    
    # Get analysis statistics
    print("\nAnalysis Statistics:")
    print("-" * 40)
    
    # Count by analysis tier
    analysis_stats = supabase.table('crypto_calls') \
        .select('analysis_tier') \
        .not_.is_('analysis_tier', 'null') \
        .execute()
    
    tier_counts = {}
    for row in analysis_stats.data:
        tier = row.get('analysis_tier', 'Unknown')
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
    
    print("Claude Analysis Tiers:")
    for tier, count in sorted(tier_counts.items()):
        print(f"  {tier}: {count:,}")
    
    # Count by X analysis tier
    x_analysis_stats = supabase.table('crypto_calls') \
        .select('x_analysis_tier') \
        .not_.is_('x_analysis_tier', 'null') \
        .execute()
    
    x_tier_counts = {}
    for row in x_analysis_stats.data:
        tier = row.get('x_analysis_tier', 'Unknown')
        x_tier_counts[tier] = x_tier_counts.get(tier, 0) + 1
    
    print("\nX/Twitter Analysis Tiers:")
    for tier, count in sorted(x_tier_counts.items()):
        print(f"  {tier}: {count:,}")
    
    # Get sample of recent analyzed calls
    print("\nSample of Recent Analyzed Calls:")
    print("-" * 40)
    
    recent_analyzed = supabase.table('crypto_calls') \
        .select('ticker, analysis_tier, x_analysis_tier, created_at') \
        .not_.is_('analysis_tier', 'null') \
        .order('created_at', desc=True) \
        .limit(5) \
        .execute()
    
    for call in recent_analyzed.data:
        print(f"Ticker: {call['ticker']}")
        print(f"  Claude: {call['analysis_tier']}")
        print(f"  X: {call.get('x_analysis_tier', 'N/A')}")
        print(f"  Date: {call['created_at']}")
        print()
    
    # Check notification counts
    notified_result = supabase.table('crypto_calls') \
        .select('notified, notified_premium') \
        .eq('notified', True) \
        .execute()
    
    premium_result = supabase.table('crypto_calls') \
        .select('notified_premium') \
        .eq('notified_premium', True) \
        .execute()
    
    print(f"Regular notifications sent: {len(notified_result.data):,}")
    print(f"Premium notifications sent: {len(premium_result.data):,}")
    
except Exception as e:
    print(f"Error accessing Supabase: {e}")
    print("\nPossible issues:")
    print("1. Table 'crypto_calls' might not exist")
    print("2. Invalid credentials")
    print("3. Network connection issue")