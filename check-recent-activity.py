#!/usr/bin/env python3
"""
Check for recent analysis activity after enabling cron jobs
"""

import requests
from datetime import datetime, timedelta
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

print("🔍 CHECKING FOR NEW ANALYSIS ACTIVITY")
print("=" * 45)

# Check recent analysis activity (last 10 minutes)
ten_minutes_ago = (datetime.utcnow() - timedelta(minutes=10)).isoformat() + 'Z'

print(f"⏰ Checking for activity since: {ten_minutes_ago}")

# Recent call analyses
recent_call_analyses = query_supabase({
    'analyzed_at': f'gte.{ten_minutes_ago}',
    'order': 'analyzed_at.desc',
    'limit': '10',
    'select': 'krom_id,ticker,analysis_score,analyzed_at'
})

print(f"\n📊 Call analyses in last 10 minutes: {len(recent_call_analyses)}")
if recent_call_analyses:
    for call in recent_call_analyses:
        analyzed_time = call.get('analyzed_at', 'Unknown')
        if analyzed_time != 'Unknown':
            try:
                dt = datetime.fromisoformat(analyzed_time.replace('Z', '+00:00'))
                analyzed_time = dt.strftime('%H:%M:%S UTC')
            except:
                pass
        
        print(f"  • {call.get('ticker', 'N/A'):10} Score: {call.get('analysis_score', 'N/A')} at {analyzed_time}")

# Recent X analyses
recent_x_analyses = query_supabase({
    'x_analyzed_at': f'gte.{ten_minutes_ago}',
    'order': 'x_analyzed_at.desc',
    'limit': '10',
    'select': 'krom_id,ticker,x_analysis_score,x_analyzed_at'
})

print(f"\n🐦 X analyses in last 10 minutes: {len(recent_x_analyses)}")
if recent_x_analyses:
    for call in recent_x_analyses:
        x_analyzed_time = call.get('x_analyzed_at', 'Unknown')
        if x_analyzed_time != 'Unknown':
            try:
                dt = datetime.fromisoformat(x_analyzed_time.replace('Z', '+00:00'))
                x_analyzed_time = dt.strftime('%H:%M:%S UTC')
            except:
                pass
        
        print(f"  • {call.get('ticker', 'N/A'):10} Score: {call.get('x_analysis_score', 'N/A')} at {x_analyzed_time}")

# Current counts
total_unanalyzed = count_records({'analysis_score': 'is.null'})
total_x_unanalyzed = count_records({'x_analysis_score': 'is.null'})

print(f"\n📈 CURRENT STATUS:")
print(f"   Calls needing analysis: {total_unanalyzed}")
print(f"   Calls needing X analysis: {total_x_unanalyzed}")

# If no recent activity, manually test one endpoint
if not recent_call_analyses and not recent_x_analyses:
    print(f"\n🧪 No recent activity detected. Testing call analysis endpoint manually...")
    
    # Test the call analysis endpoint directly
    try:
        test_url = "https://lively-torrone-8199e0.netlify.app/api/cron/analyze"
        test_params = {'auth': 'a07066e62da04a115fde8f18813a931b16095bbaa2fac17dfd6cd0d9662ae30b'}
        
        print(f"   Testing: {test_url}")
        test_response = requests.post(test_url, params=test_params, timeout=30)
        
        if test_response.status_code == 200:
            result = test_response.json()
            print(f"   ✅ Test successful: {result}")
        else:
            print(f"   ❌ Test failed: {test_response.status_code} - {test_response.text[:200]}")
    
    except Exception as e:
        print(f"   ❌ Test error: {str(e)}")

print("=" * 45)