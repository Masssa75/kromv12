#!/usr/bin/env python3
"""
Check current analysis status after CRON_SECRET fix
"""

import requests
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

headers = {
    'apikey': SUPABASE_SERVICE_ROLE_KEY,
    'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

def query_supabase(query_params):
    """Execute a query against Supabase"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    response = requests.get(url, headers=headers, params=query_params)
    response.raise_for_status()
    return response.json()

def count_records(query_params):
    """Count records matching query"""
    headers_count = headers.copy()
    headers_count['Prefer'] = 'count=exact'
    
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    response = requests.get(url, headers=headers_count, params=query_params)
    response.raise_for_status()
    
    # Get count from Content-Range header
    content_range = response.headers.get('Content-Range', '')
    if '/' in content_range:
        return int(content_range.split('/')[-1])
    return 0

print("🔍 ANALYSIS SYSTEM STATUS CHECK")
print("=" * 50)

# 1. Total calls in database
total_calls = count_records({})
print(f"📊 Total calls in database: {total_calls:,}")

# 2. Calls with analysis (analysis_score IS NOT NULL)
analyzed_calls = count_records({'analysis_score': 'not.is.null'})
print(f"✅ Calls with analysis: {analyzed_calls:,}")

# 3. Calls needing analysis (analysis_score IS NULL)
unanalyzed_calls = count_records({'analysis_score': 'is.null'})
print(f"⏳ Calls needing analysis: {unanalyzed_calls:,}")

# 4. Analysis completion percentage
completion_pct = (analyzed_calls / total_calls * 100) if total_calls > 0 else 0
print(f"📈 Analysis completion: {completion_pct:.1f}%")

print("\n🗓️ AUGUST 2025 ANALYSIS STATUS")
print("-" * 30)

# 5. August 2025 calls
august_calls = count_records({
    'buy_timestamp': 'gte.2025-08-01T00:00:00Z',
    'buy_timestamp': 'lt.2025-09-01T00:00:00Z'
})
print(f"📅 Total August 2025 calls: {august_calls:,}")

# 6. August 2025 analyzed calls
august_analyzed = count_records({
    'buy_timestamp': 'gte.2025-08-01T00:00:00Z',
    'buy_timestamp': 'lt.2025-09-01T00:00:00Z',
    'analysis_score': 'not.is.null'
})
print(f"✅ August 2025 analyzed: {august_analyzed:,}")

# 7. August 2025 unanalyzed calls
august_unanalyzed = count_records({
    'buy_timestamp': 'gte.2025-08-01T00:00:00Z',
    'buy_timestamp': 'lt.2025-09-01T00:00:00Z',
    'analysis_score': 'is.null'
})
print(f"⏳ August 2025 needing analysis: {august_unanalyzed:,}")

# 8. August completion percentage
august_completion = (august_analyzed / august_calls * 100) if august_calls > 0 else 0
print(f"📈 August analysis completion: {august_completion:.1f}%")

print("\n🐦 X (TWITTER) ANALYSIS STATUS")
print("-" * 30)

# 9. X analysis stats
x_analyzed = count_records({'x_analysis_score': 'not.is.null'})
x_unanalyzed = count_records({'x_analysis_score': 'is.null'})
x_completion = (x_analyzed / total_calls * 100) if total_calls > 0 else 0

print(f"✅ Calls with X analysis: {x_analyzed:,}")
print(f"⏳ Calls needing X analysis: {x_unanalyzed:,}")
print(f"📈 X analysis completion: {x_completion:.1f}%")

print("\n🕐 RECENT ANALYSIS ACTIVITY")
print("-" * 30)

# 10. Most recent analyzed calls
recent_analyzed = query_supabase({
    'analysis_score': 'not.is.null',
    'order': 'analyzed_at.desc',
    'limit': '5',
    'select': 'krom_id,ticker,analysis_score,analysis_model,analyzed_at,buy_timestamp'
})

if recent_analyzed:
    print("Last 5 analyzed calls:")
    for call in recent_analyzed:
        analyzed_time = call.get('analyzed_at', 'Unknown')
        if analyzed_time and analyzed_time != 'Unknown':
            # Parse and format the timestamp
            try:
                dt = datetime.fromisoformat(analyzed_time.replace('Z', '+00:00'))
                analyzed_time = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
            except:
                pass
        
        print(f"  • {call.get('ticker', 'N/A'):8} Score: {call.get('analysis_score', 'N/A'):2} "
              f"Model: {call.get('analysis_model', 'N/A'):20} "
              f"Analyzed: {analyzed_time}")
else:
    print("No recent analyzed calls found")

# 11. Most recent X analyzed calls
recent_x_analyzed = query_supabase({
    'x_analysis_score': 'not.is.null',
    'order': 'x_analyzed_at.desc',
    'limit': '5',
    'select': 'krom_id,ticker,x_analysis_score,x_analysis_model,x_analyzed_at'
})

if recent_x_analyzed:
    print("\nLast 5 X analyzed calls:")
    for call in recent_x_analyzed:
        x_analyzed_time = call.get('x_analyzed_at', 'Unknown')
        if x_analyzed_time and x_analyzed_time != 'Unknown':
            try:
                dt = datetime.fromisoformat(x_analyzed_time.replace('Z', '+00:00'))
                x_analyzed_time = dt.strftime('%Y-%m-%d %H:%M:%S UTC')
            except:
                pass
        
        print(f"  • {call.get('ticker', 'N/A'):8} Score: {call.get('x_analysis_score', 'N/A'):2} "
              f"Model: {call.get('x_analysis_model', 'N/A'):20} "
              f"X Analyzed: {x_analyzed_time}")
else:
    print("No recent X analyzed calls found")

# 12. Calls that need analysis (next to be processed)
print("\n⏭️ NEXT CALLS TO BE ANALYZED")
print("-" * 30)

next_to_analyze = query_supabase({
    'analysis_score': 'is.null',
    'order': 'created_at.asc',
    'limit': '5',
    'select': 'krom_id,ticker,buy_timestamp,created_at'
})

if next_to_analyze:
    print("Next 5 calls waiting for analysis:")
    for call in next_to_analyze:
        buy_time = call.get('buy_timestamp', 'Unknown')
        if buy_time and buy_time != 'Unknown':
            try:
                dt = datetime.fromisoformat(buy_time.replace('Z', '+00:00'))
                buy_time = dt.strftime('%Y-%m-%d %H:%M UTC')
            except:
                pass
        
        print(f"  • {call.get('ticker', 'N/A'):8} ID: {call.get('krom_id', 'N/A'):6} "
              f"Buy: {buy_time}")
else:
    print("No calls waiting for analysis")

print("\n" + "=" * 50)
print("Status check complete!")