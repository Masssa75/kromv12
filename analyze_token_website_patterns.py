#!/usr/bin/env python3
"""
Analyze website addition patterns for token discovery system.
Understand when and how tokens add websites after launch.
"""

import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import json
from supabase import create_client
from dotenv import load_dotenv
import pandas as pd
import numpy as np

# Load environment variables
load_dotenv()

# Initialize Supabase client with service role key for RLS
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

def get_token_statistics():
    """Get comprehensive statistics about tokens in the database."""
    print("=" * 80)
    print("TOKEN DISCOVERY SYSTEM - WEBSITE ANALYSIS")
    print("=" * 80)
    
    # Get total token count
    total_response = supabase.table('token_discovery').select('id', count='exact').execute()
    total_tokens = total_response.count
    
    # Get tokens with websites
    with_website = supabase.table('token_discovery').select('*').not_.is_('website_url', 'null').execute()
    tokens_with_website = len(with_website.data)
    
    # Get tokens by network
    all_tokens = supabase.table('token_discovery').select('network, first_seen_at, website_url, initial_liquidity_usd, symbol, name').execute()
    
    df = pd.DataFrame(all_tokens.data)
    
    print(f"\n📊 OVERALL STATISTICS")
    print(f"{'='*40}")
    print(f"Total tokens tracked: {total_tokens:,}")
    print(f"Tokens with websites: {tokens_with_website:,} ({tokens_with_website/total_tokens*100:.2f}%)")
    print(f"Tokens without websites: {total_tokens - tokens_with_website:,} ({(total_tokens - tokens_with_website)/total_tokens*100:.2f}%)")
    
    # Network breakdown
    print(f"\n🌐 NETWORK DISTRIBUTION")
    print(f"{'='*40}")
    network_counts = df['network'].value_counts()
    for network, count in network_counts.items():
        website_count = len(df[(df['network'] == network) & (df['website_url'].notna())])
        print(f"{network:12} {count:7,} tokens | {website_count:4} with websites ({website_count/count*100:.2f}%)")
    
    # Time analysis
    print(f"\n⏰ TIME ANALYSIS")
    print(f"{'='*40}")
    
    # Convert timestamps (handle timezone-aware datetime)
    df['first_seen_at'] = pd.to_datetime(df['first_seen_at'], utc=True)
    now = pd.Timestamp.now(tz='UTC')
    
    # Calculate age of tokens
    df['age_hours'] = (now - df['first_seen_at']).dt.total_seconds() / 3600
    
    # Age buckets
    age_buckets = [
        (0, 1, "< 1 hour"),
        (1, 4, "1-4 hours"),
        (4, 12, "4-12 hours"),
        (12, 24, "12-24 hours"),
        (24, 48, "24-48 hours"),
        (48, 72, "48-72 hours"),
        (72, 168, "3-7 days"),
        (168, float('inf'), "> 7 days")
    ]
    
    print("Token age distribution and website presence:")
    for min_hours, max_hours, label in age_buckets:
        bucket_tokens = df[(df['age_hours'] >= min_hours) & (df['age_hours'] < max_hours)]
        if len(bucket_tokens) > 0:
            with_website = len(bucket_tokens[bucket_tokens['website_url'].notna()])
            print(f"{label:15} {len(bucket_tokens):7,} tokens | {with_website:4} with websites ({with_website/len(bucket_tokens)*100:.2f}%)")
    
    # Liquidity analysis
    print(f"\n💰 LIQUIDITY ANALYSIS")
    print(f"{'='*40}")
    
    # Filter out nulls for liquidity analysis
    df_with_liq = df[df['initial_liquidity_usd'].notna()].copy()
    df_with_liq['initial_liquidity_usd'] = pd.to_numeric(df_with_liq['initial_liquidity_usd'])
    
    liquidity_buckets = [
        (0, 1000, "$0-1K"),
        (1000, 5000, "$1K-5K"),
        (5000, 10000, "$5K-10K"),
        (10000, 50000, "$10K-50K"),
        (50000, 100000, "$50K-100K"),
        (100000, float('inf'), "> $100K")
    ]
    
    print("Website presence by initial liquidity:")
    for min_liq, max_liq, label in liquidity_buckets:
        bucket_tokens = df_with_liq[(df_with_liq['initial_liquidity_usd'] >= min_liq) & 
                                     (df_with_liq['initial_liquidity_usd'] < max_liq)]
        if len(bucket_tokens) > 0:
            with_website = len(bucket_tokens[bucket_tokens['website_url'].notna()])
            print(f"{label:15} {len(bucket_tokens):7,} tokens | {with_website:4} with websites ({with_website/len(bucket_tokens)*100:.2f}%)")
    
    # Sample of tokens with websites
    print(f"\n🔍 SAMPLE TOKENS WITH WEBSITES")
    print(f"{'='*40}")
    
    tokens_with_sites = df[df['website_url'].notna()].head(10)
    for _, token in tokens_with_sites.iterrows():
        token_time = pd.to_datetime(token['first_seen_at'], utc=True) if not isinstance(token['first_seen_at'], pd.Timestamp) else token['first_seen_at']
        age = (now - token_time).total_seconds() / 3600
        liq = token['initial_liquidity_usd']
        liq_str = f"${liq:,.0f}" if pd.notna(liq) else "Unknown"
        print(f"{token['symbol']:8} | {token['network']:8} | Age: {age:5.1f}h | Liquidity: {liq_str:>10}")
    
    return df

def analyze_website_checking_patterns(df):
    """Analyze patterns to determine optimal checking schedule."""
    print(f"\n🎯 RECOMMENDED CHECKING STRATEGY")
    print(f"{'='*80}")
    
    # Calculate website rates by age (handle timezone)
    df['first_seen_at'] = pd.to_datetime(df['first_seen_at'], utc=True)
    now = pd.Timestamp.now(tz='UTC')
    df['age_hours'] = (now - df['first_seen_at']).dt.total_seconds() / 3600
    
    # Key findings
    young_tokens = df[df['age_hours'] < 24]
    old_tokens = df[df['age_hours'] > 168]  # > 7 days
    
    young_with_website = len(young_tokens[young_tokens['website_url'].notna()])
    old_with_website = len(old_tokens[old_tokens['website_url'].notna()])
    
    print(f"\n📈 KEY INSIGHTS:")
    if len(young_tokens) > 0:
        print(f"- Tokens < 24h old: {young_with_website}/{len(young_tokens)} have websites ({young_with_website/len(young_tokens)*100:.2f}%)")
    else:
        print(f"- Tokens < 24h old: No data yet")
    
    if len(old_tokens) > 0:
        print(f"- Tokens > 7 days old: {old_with_website}/{len(old_tokens)} have websites ({old_with_website/len(old_tokens)*100:.2f}%)")
    else:
        print(f"- Tokens > 7 days old: No tokens old enough yet (system started ~48h ago)")
    
    # Network-specific patterns
    print(f"\n🌐 NETWORK-SPECIFIC PATTERNS:")
    for network in df['network'].value_counts().head(5).index:
        network_df = df[df['network'] == network]
        with_website = len(network_df[network_df['website_url'].notna()])
        
        # High liquidity tokens
        high_liq = network_df[pd.to_numeric(network_df['initial_liquidity_usd'], errors='coerce') > 10000]
        high_liq_with_website = len(high_liq[high_liq['website_url'].notna()])
        
        print(f"\n{network}:")
        print(f"  Overall: {with_website}/{len(network_df)} have websites ({with_website/len(network_df)*100:.2f}%)")
        if len(high_liq) > 0:
            print(f"  High liquidity (>$10K): {high_liq_with_website}/{len(high_liq)} have websites ({high_liq_with_website/len(high_liq)*100:.2f}%)")
    
    print(f"\n💡 RECOMMENDED CHECKING SCHEDULE:")
    print(f"{'='*40}")
    print("""
Based on current data (limited by single check):

1. IMMEDIATE (0-1 hour): Check once for high liquidity tokens (>$50K)
   - These are more likely to be legitimate projects

2. SHORT TERM (1-24 hours): Check at 1h, 6h, 12h, 24h
   - Most legitimate projects add websites within first day
   
3. MEDIUM TERM (1-3 days): Check at 48h, 72h
   - Catch slower projects that add sites after initial launch
   
4. LONG TERM (3-7 days): Final check at 7 days
   - Last chance check before marking as "no website expected"

5. PRIORITY TIERS:
   - Tier 1 (check frequently): Liquidity > $50K, Ethereum/Base/Arbitrum
   - Tier 2 (normal schedule): Liquidity $10K-$50K, any network
   - Tier 3 (minimal checks): Liquidity < $10K, Solana memecoins
   
Note: We need to implement re-checking to get better data on WHEN websites are added!
""")

def estimate_api_usage():
    """Estimate API usage with different checking strategies."""
    print(f"\n📊 API USAGE ESTIMATION")
    print(f"{'='*80}")
    
    # Current rate: ~800 tokens/hour = 19,200/day
    new_tokens_per_day = 19200
    
    # Scenario 1: Check all tokens at all intervals
    checks_per_token_aggressive = 8  # 1h, 4h, 12h, 24h, 48h, 72h, 7d, 14d
    
    # Scenario 2: Smart checking based on liquidity
    # Assume 5% high liquidity (8 checks), 15% medium (5 checks), 80% low (2 checks)
    checks_per_token_smart = (0.05 * 8) + (0.15 * 5) + (0.80 * 2)
    
    # Scenario 3: Current (single check)
    checks_per_token_current = 1
    
    print(f"Daily new tokens: {new_tokens_per_day:,}")
    print(f"\nAPI calls per day (30 tokens per call):")
    print(f"- Current (1 check): {new_tokens_per_day * checks_per_token_current / 30:,.0f} calls")
    print(f"- Smart strategy: {new_tokens_per_day * checks_per_token_smart / 30:,.0f} calls")
    print(f"- Aggressive (all): {new_tokens_per_day * checks_per_token_aggressive / 30:,.0f} calls")
    
    print(f"\nWith 10-minute cron (144 runs/day):")
    print(f"- Current: {new_tokens_per_day * checks_per_token_current / 30 / 144:.1f} calls per run")
    print(f"- Smart: {new_tokens_per_day * checks_per_token_smart / 30 / 144:.1f} calls per run")
    print(f"- Aggressive: {new_tokens_per_day * checks_per_token_aggressive / 30 / 144:.1f} calls per run")

if __name__ == "__main__":
    # Get and analyze data
    df = get_token_statistics()
    analyze_website_checking_patterns(df)
    estimate_api_usage()
    
    print(f"\n{'='*80}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*80}")