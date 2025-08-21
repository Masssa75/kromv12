#!/usr/bin/env python3
"""
Check for tokens with missing market cap data that were added ~9 hours ago
"""

import os
from datetime import datetime, timedelta
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, service_key)

# Get tokens created in the last 12 hours
twelve_hours_ago = datetime.utcnow() - timedelta(hours=12)
six_hours_ago = datetime.utcnow() - timedelta(hours=6)

print("Checking tokens added 6-12 hours ago...")
print("=" * 60)

try:
    # Get recent tokens
    response = supabase.table("crypto_calls").select(
        "ticker, created_at, source, price_at_call, market_cap_at_call, current_price, "
        "current_market_cap, ath_price, ath_market_cap, liquidity_usd, roi_percent, ath_roi_percent"
    ).gte("created_at", twelve_hours_ago.isoformat()).lte("created_at", six_hours_ago.isoformat()).order("created_at", desc=True).execute()
    
    tokens = response.data
    print(f"Found {len(tokens)} tokens from 6-12 hours ago\n")
    
    # Count issues
    missing_entry_mc = 0
    missing_current_mc = 0
    missing_ath_mc = 0
    missing_roi = 0
    gt_trending_count = 0
    
    print("Sample of problematic tokens:")
    print("-" * 60)
    
    for token in tokens[:20]:  # Show first 20
        # Handle different timestamp formats
        created_str = token['created_at'].split('+')[0].split('.')[0]  # Remove timezone and microseconds
        created_dt = datetime.fromisoformat(created_str)
        hours_ago = (datetime.utcnow() - created_dt).total_seconds() / 3600
        
        has_issue = False
        issues = []
        
        if not token['market_cap_at_call']:
            missing_entry_mc += 1
            issues.append("No Entry MC")
            has_issue = True
            
        if not token['current_market_cap']:
            missing_current_mc += 1
            issues.append("No Current MC")
            has_issue = True
            
        if not token['ath_market_cap']:
            missing_ath_mc += 1
            issues.append("No ATH MC")
            has_issue = True
            
        if token['roi_percent'] is None:
            missing_roi += 1
            issues.append("No ROI")
            has_issue = True
            
        if token['source'] == 'gecko_trending':
            gt_trending_count += 1
            
        if has_issue:
            print(f"{token['ticker']:<10} ({hours_ago:.1f}h ago) - Source: {token['source']:<15} Issues: {', '.join(issues)}")
            print(f"  Entry MC: {token['market_cap_at_call']}, Current MC: {token['current_market_cap']}")
            print(f"  Price at call: {token['price_at_call']}, Current price: {token['current_price']}")
            print()
    
    print("\nSummary:")
    print("-" * 60)
    print(f"Total tokens checked: {len(tokens)}")
    print(f"Missing Entry Market Cap: {missing_entry_mc} ({missing_entry_mc/len(tokens)*100:.1f}%)")
    print(f"Missing Current Market Cap: {missing_current_mc} ({missing_current_mc/len(tokens)*100:.1f}%)")
    print(f"Missing ATH Market Cap: {missing_ath_mc} ({missing_ath_mc/len(tokens)*100:.1f}%)")
    print(f"Missing ROI: {missing_roi} ({missing_roi/len(tokens)*100:.1f}%)")
    print(f"GT Trending tokens: {gt_trending_count}")
    
    # Check the most recent tokens (last hour)
    print("\n" + "=" * 60)
    print("Checking most recent tokens (last hour)...")
    
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent = supabase.table("crypto_calls").select(
        "ticker, created_at, source, market_cap_at_call, current_market_cap"
    ).gte("created_at", one_hour_ago.isoformat()).order("created_at", desc=True).limit(10).execute()
    
    print(f"\nLast 10 tokens added:")
    for token in recent.data:
        created_str = token['created_at'].split('+')[0].split('.')[0]
        created_dt = datetime.fromisoformat(created_str)
        mins_ago = (datetime.utcnow() - created_dt).total_seconds() / 60
        entry_mc = token['market_cap_at_call'] or 'N/A'
        current_mc = token['current_market_cap'] or 'N/A'
        print(f"{token['ticker']:<10} ({mins_ago:.0f}m ago) - Source: {token['source']:<15} Entry MC: {entry_mc:<15} Current MC: {current_mc}")
        
except Exception as e:
    print(f"Error: {e}")