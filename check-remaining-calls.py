#!/usr/bin/env python3
"""
Check details on remaining unanalyzed calls
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
    'Content-Type': 'application/json'
}

def query_supabase(query_params):
    """Execute a query against Supabase"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    response = requests.get(url, headers=headers, params=query_params)
    response.raise_for_status()
    return response.json()

print("🔍 REMAINING UNANALYZED CALLS DETAILS")
print("=" * 60)

# Get all unanalyzed calls
unanalyzed = query_supabase({
    'analysis_score': 'is.null',
    'order': 'created_at.asc',
    'limit': '50',
    'select': 'krom_id,ticker,buy_timestamp,created_at,raw_data'
})

print(f"Found {len(unanalyzed)} unanalyzed calls")
print()

for i, call in enumerate(unanalyzed[:20], 1):  # Show first 20
    ticker = call.get('ticker', 'N/A')
    krom_id = call.get('krom_id', 'N/A')
    buy_timestamp = call.get('buy_timestamp')
    created_at = call.get('created_at')
    
    # Format timestamps
    buy_time_str = "None"
    if buy_timestamp:
        try:
            dt = datetime.fromisoformat(buy_timestamp.replace('Z', '+00:00'))
            buy_time_str = dt.strftime('%Y-%m-%d %H:%M UTC')
        except:
            buy_time_str = str(buy_timestamp)
    
    created_time_str = "None"
    if created_at:
        try:
            dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            created_time_str = dt.strftime('%Y-%m-%d %H:%M UTC')
        except:
            created_time_str = str(created_at)
    
    # Check if raw_data has token info
    raw_data = call.get('raw_data', {})
    has_token_data = bool(raw_data and isinstance(raw_data, dict) and raw_data.get('token'))
    
    print(f"{i:2}. {ticker:10} | ID: {krom_id} | Created: {created_time_str} | Buy: {buy_time_str} | Token data: {has_token_data}")

if len(unanalyzed) > 20:
    print(f"\n... and {len(unanalyzed) - 20} more unanalyzed calls")

# Check for any recent activity (calls created in last 24 hours)
print("\n🕐 RECENT CALL ACTIVITY (Last 24 hours)")
print("-" * 40)

from datetime import datetime, timedelta
yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat() + 'Z'

recent_calls = query_supabase({
    'created_at': f'gte.{yesterday}',
    'order': 'created_at.desc',
    'limit': '10',
    'select': 'krom_id,ticker,created_at,analysis_score,x_analysis_score'
})

if recent_calls:
    print(f"Found {len(recent_calls)} calls created in last 24 hours:")
    for call in recent_calls:
        ticker = call.get('ticker', 'N/A')
        created_at = call.get('created_at', 'N/A')
        analysis_score = call.get('analysis_score')
        x_analysis_score = call.get('x_analysis_score')
        
        if created_at != 'N/A':
            try:
                dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                created_at = dt.strftime('%Y-%m-%d %H:%M UTC')
            except:
                pass
        
        analysis_status = "✅" if analysis_score is not None else "⏳"
        x_status = "✅" if x_analysis_score is not None else "⏳"
        
        print(f"  • {ticker:10} | {created_at} | Analysis: {analysis_status} | X: {x_status}")
else:
    print("No calls created in last 24 hours")