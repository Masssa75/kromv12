#!/usr/bin/env python3
"""
Analyze website addition timing patterns after smart re-checking implementation.
Track when tokens add websites and provide actionable insights.
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

def analyze_website_timing():
    """Analyze when tokens add websites after launch."""
    print("=" * 80)
    print("WEBSITE ADDITION TIMING ANALYSIS")
    print("=" * 80)
    
    # Get all tokens with websites that have timing data
    response = supabase.table('token_discovery').select('*').not_.is_('website_found_at', 'null').execute()
    tokens_with_timing = pd.DataFrame(response.data)
    
    if len(tokens_with_timing) == 0:
        print("\n⚠️ No tokens with website timing data yet.")
        print("The smart re-checking system needs time to discover websites.")
        print("Run this script again after a few hours.")
        return
    
    # Convert timestamps
    tokens_with_timing['first_seen_at'] = pd.to_datetime(tokens_with_timing['first_seen_at'], utc=True)
    tokens_with_timing['website_found_at'] = pd.to_datetime(tokens_with_timing['website_found_at'], utc=True)
    
    # Calculate time to website
    tokens_with_timing['hours_to_website'] = (
        tokens_with_timing['website_found_at'] - tokens_with_timing['first_seen_at']
    ).dt.total_seconds() / 3600
    
    print(f"\n📊 WEBSITE TIMING STATISTICS")
    print(f"{'='*40}")
    print(f"Tokens with website timing data: {len(tokens_with_timing)}")
    print(f"Average time to add website: {tokens_with_timing['hours_to_website'].mean():.1f} hours")
    print(f"Median time to add website: {tokens_with_timing['hours_to_website'].median():.1f} hours")
    print(f"Fastest website addition: {tokens_with_timing['hours_to_website'].min():.1f} hours")
    print(f"Slowest website addition: {tokens_with_timing['hours_to_website'].max():.1f} hours")
    
    # Percentile analysis
    print(f"\n📈 PERCENTILE ANALYSIS")
    print(f"{'='*40}")
    percentiles = [10, 25, 50, 75, 90, 95, 99]
    for p in percentiles:
        value = np.percentile(tokens_with_timing['hours_to_website'], p)
        print(f"{p:3d}% of tokens add website within {value:.1f} hours")
    
    # Time bucket analysis
    print(f"\n⏰ TIME BUCKET ANALYSIS")
    print(f"{'='*40}")
    
    time_buckets = [
        (0, 1, "< 1 hour"),
        (1, 4, "1-4 hours"),
        (4, 12, "4-12 hours"),
        (12, 24, "12-24 hours"),
        (24, 48, "24-48 hours"),
        (48, 72, "48-72 hours"),
        (72, 168, "3-7 days"),
        (168, float('inf'), "> 7 days")
    ]
    
    for min_hours, max_hours, label in time_buckets:
        count = len(tokens_with_timing[
            (tokens_with_timing['hours_to_website'] >= min_hours) & 
            (tokens_with_timing['hours_to_website'] < max_hours)
        ])
        if count > 0:
            pct = count / len(tokens_with_timing) * 100
            print(f"{label:15} {count:4} tokens ({pct:5.1f}%)")
    
    # Check count analysis
    print(f"\n🔄 CHECK COUNT ANALYSIS")
    print(f"{'='*40}")
    check_counts = tokens_with_timing['website_check_count'].value_counts().sort_index()
    for checks, count in check_counts.items():
        pct = count / len(tokens_with_timing) * 100
        print(f"Found on check #{checks}: {count:4} tokens ({pct:5.1f}%)")
    
    # Network analysis
    print(f"\n🌐 NETWORK ANALYSIS")
    print(f"{'='*40}")
    for network in tokens_with_timing['network'].unique():
        network_data = tokens_with_timing[tokens_with_timing['network'] == network]
        if len(network_data) > 0:
            avg_time = network_data['hours_to_website'].mean()
            median_time = network_data['hours_to_website'].median()
            print(f"{network:10} Avg: {avg_time:5.1f}h | Median: {median_time:5.1f}h | Count: {len(network_data)}")
    
    # Liquidity analysis
    print(f"\n💰 LIQUIDITY CORRELATION")
    print(f"{'='*40}")
    
    # Filter tokens with liquidity data
    with_liquidity = tokens_with_timing[tokens_with_timing['initial_liquidity_usd'].notna()].copy()
    with_liquidity['initial_liquidity_usd'] = pd.to_numeric(with_liquidity['initial_liquidity_usd'])
    
    liquidity_buckets = [
        (0, 10000, "$0-10K"),
        (10000, 50000, "$10K-50K"),
        (50000, 100000, "$50K-100K"),
        (100000, float('inf'), "> $100K")
    ]
    
    for min_liq, max_liq, label in liquidity_buckets:
        bucket_data = with_liquidity[
            (with_liquidity['initial_liquidity_usd'] >= min_liq) & 
            (with_liquidity['initial_liquidity_usd'] < max_liq)
        ]
        if len(bucket_data) > 0:
            avg_time = bucket_data['hours_to_website'].mean()
            median_time = bucket_data['hours_to_website'].median()
            print(f"{label:10} Avg: {avg_time:5.1f}h | Median: {median_time:5.1f}h | Count: {len(bucket_data)}")

def analyze_checking_efficiency():
    """Analyze the efficiency of the checking schedule."""
    print(f"\n🎯 CHECKING EFFICIENCY ANALYSIS")
    print(f"{'='*80}")
    
    # Get all tokens that have been checked
    response = supabase.table('token_discovery').select('*').not_.is_('website_check_count', 'null').execute()
    all_checked = pd.DataFrame(response.data)
    
    if len(all_checked) == 0:
        print("No tokens have been checked yet.")
        return
    
    # Overall stats
    total_checks = all_checked['website_check_count'].sum()
    tokens_with_website = len(all_checked[all_checked['website_url'].notna()])
    tokens_without_website = len(all_checked) - tokens_with_website
    
    print(f"Total tokens checked: {len(all_checked):,}")
    print(f"Total check operations: {total_checks:,}")
    print(f"Average checks per token: {total_checks/len(all_checked):.2f}")
    print(f"Tokens with website: {tokens_with_website:,} ({tokens_with_website/len(all_checked)*100:.1f}%)")
    print(f"Tokens without website: {tokens_without_website:,} ({tokens_without_website/len(all_checked)*100:.1f}%)")
    
    # Efficiency metrics
    print(f"\n📊 EFFICIENCY METRICS")
    print(f"{'='*40}")
    
    # Calculate wasted checks (tokens that never got a website after multiple checks)
    max_checked_no_website = all_checked[all_checked['website_url'].isna()]['website_check_count'].max()
    avg_checks_no_website = all_checked[all_checked['website_url'].isna()]['website_check_count'].mean()
    
    print(f"Max checks on token without website: {max_checked_no_website}")
    print(f"Avg checks on tokens without website: {avg_checks_no_website:.2f}")
    
    if tokens_with_website > 0:
        avg_checks_with_website = all_checked[all_checked['website_url'].notna()]['website_check_count'].mean()
        print(f"Avg checks to find website: {avg_checks_with_website:.2f}")
    
    # Check distribution
    print(f"\n📈 CHECK DISTRIBUTION")
    print(f"{'='*40}")
    check_distribution = all_checked['website_check_count'].value_counts().sort_index()
    for checks, count in check_distribution.head(10).items():
        pct = count / len(all_checked) * 100
        print(f"{checks} checks: {count:5,} tokens ({pct:5.1f}%)")

def generate_recommendations():
    """Generate recommendations based on the analysis."""
    print(f"\n💡 RECOMMENDATIONS")
    print(f"{'='*80}")
    
    # Get statistics for recommendations
    response = supabase.table('token_discovery').select('*').not_.is_('website_found_at', 'null').execute()
    tokens_with_timing = pd.DataFrame(response.data)
    
    if len(tokens_with_timing) > 0:
        tokens_with_timing['first_seen_at'] = pd.to_datetime(tokens_with_timing['first_seen_at'], utc=True)
        tokens_with_timing['website_found_at'] = pd.to_datetime(tokens_with_timing['website_found_at'], utc=True)
        tokens_with_timing['hours_to_website'] = (
            tokens_with_timing['website_found_at'] - tokens_with_timing['first_seen_at']
        ).dt.total_seconds() / 3600
        
        median_time = tokens_with_timing['hours_to_website'].median()
        percentile_90 = np.percentile(tokens_with_timing['hours_to_website'], 90)
        
        print(f"\nBased on {len(tokens_with_timing)} tokens with website timing data:")
        print(f"• 50% of tokens add websites within {median_time:.1f} hours")
        print(f"• 90% of tokens add websites within {percentile_90:.1f} hours")
        print(f"\nOPTIMAL CHECKING SCHEDULE:")
        print(f"1. High Priority (>$50K liquidity): Check at 15m, 30m, 1h, 2h, 4h, 8h")
        print(f"2. Normal Priority: Check at 1h, 4h, 12h, 24h, 48h")
        print(f"3. Stop checking after {percentile_90:.0f} hours or 6 checks")
    else:
        print("\n⚠️ Insufficient data for recommendations.")
        print("The system needs to run for a few hours to gather timing data.")
    
    # API usage projection
    print(f"\n📊 API USAGE PROJECTION")
    print(f"{'='*40}")
    
    # Estimate based on current data
    response = supabase.table('token_discovery').select('id', count='exact').execute()
    total_tokens = response.count
    
    response = supabase.table('token_discovery').select('id', count='exact').not_.is_('website_check_count', 'null').execute()
    checked_tokens = response.count
    
    if checked_tokens > 0:
        response = supabase.table('token_discovery').select('website_check_count').not_.is_('website_check_count', 'null').execute()
        check_data = pd.DataFrame(response.data)
        avg_checks = check_data['website_check_count'].mean()
        
        # Assuming 800 new tokens per hour
        new_tokens_per_day = 19200
        estimated_checks_per_token = avg_checks
        daily_api_calls = (new_tokens_per_day * estimated_checks_per_token) / 30  # 30 tokens per API call
        
        print(f"Current average checks per token: {avg_checks:.2f}")
        print(f"Estimated new tokens per day: {new_tokens_per_day:,}")
        print(f"Estimated API calls per day: {daily_api_calls:,.0f}")
        print(f"API calls per 10-minute cron run: {daily_api_calls/144:.1f}")

if __name__ == "__main__":
    analyze_website_timing()
    analyze_checking_efficiency()
    generate_recommendations()
    
    print(f"\n{'='*80}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*80}")
    print("\n🚀 The smart re-checking system is now active!")
    print("It will automatically discover websites as tokens add them.")
    print("Run this script periodically to track performance and patterns.")