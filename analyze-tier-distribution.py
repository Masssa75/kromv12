#!/usr/bin/env python3
"""Analyze the distribution of analysis tiers in Supabase"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv
from collections import Counter
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(url, key)

print("Analyzing tier distribution in KROMV12...")
print("=" * 60)

# Get all analyzed calls
try:
    # Get Claude analysis distribution
    claude_result = supabase.table('crypto_calls') \
        .select('analysis_tier, ticker, created_at') \
        .not_.is_('analysis_tier', 'null') \
        .execute()
    
    claude_tiers = Counter()
    for row in claude_result.data:
        claude_tiers[row['analysis_tier']] += 1
    
    print("Claude Analysis Distribution:")
    total_claude = sum(claude_tiers.values())
    for tier in ['ALPHA', 'SOLID', 'BASIC', 'TRASH']:
        count = claude_tiers.get(tier, 0)
        percentage = (count / total_claude * 100) if total_claude > 0 else 0
        print(f"  {tier}: {count:,} ({percentage:.1f}%)")
    
    # Get X analysis distribution
    x_result = supabase.table('crypto_calls') \
        .select('x_analysis_tier, ticker, created_at') \
        .not_.is_('x_analysis_tier', 'null') \
        .execute()
    
    x_tiers = Counter()
    for row in x_result.data:
        x_tiers[row['x_analysis_tier']] += 1
    
    print(f"\nX/Twitter Analysis Distribution:")
    total_x = sum(x_tiers.values())
    for tier in ['ALPHA', 'SOLID', 'BASIC', 'TRASH']:
        count = x_tiers.get(tier, 0)
        percentage = (count / total_x * 100) if total_x > 0 else 0
        print(f"  {tier}: {count:,} ({percentage:.1f}%)")
    
    # Get some examples of each tier
    print("\n" + "=" * 60)
    print("Examples by Tier:")
    
    for tier in ['ALPHA', 'SOLID', 'BASIC', 'TRASH']:
        examples = supabase.table('crypto_calls') \
            .select('ticker, analysis_tier, x_analysis_tier, analysis_description') \
            .eq('analysis_tier', tier) \
            .limit(3) \
            .execute()
        
        if examples.data:
            print(f"\n{tier} Examples:")
            for ex in examples.data:
                print(f"  {ex['ticker']}: Claude={ex['analysis_tier']}, X={ex.get('x_analysis_tier', 'N/A')}")
                if ex.get('analysis_description'):
                    desc = ex['analysis_description'][:100] + "..." if len(ex['analysis_description']) > 100 else ex['analysis_description']
                    print(f"    Description: {desc}")
    
    # Check for any calls with both ALPHA ratings
    double_alpha = supabase.table('crypto_calls') \
        .select('ticker, analysis_tier, x_analysis_tier, created_at') \
        .eq('analysis_tier', 'ALPHA') \
        .eq('x_analysis_tier', 'ALPHA') \
        .execute()
    
    print(f"\n{'=' * 60}")
    print(f"Calls with BOTH Claude and X rated as ALPHA: {len(double_alpha.data)}")
    if double_alpha.data:
        for call in double_alpha.data[:5]:
            print(f"  {call['ticker']} - {call['created_at']}")
    
except Exception as e:
    print(f"Error: {e}")