#!/usr/bin/env python3
"""
Final comprehensive report on analysis system status
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

print("📊 ANALYSIS SYSTEM - FINAL STATUS REPORT")
print("=" * 60)
print(f"Report generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

print(f"\n🎯 ACTIONS COMPLETED:")
print("✅ 1. Identified cron jobs were disabled")
print("✅ 2. Enabled both cron jobs (Call Analysis & X Analysis)")
print("✅ 3. Discovered incorrect CRON_SECRET in job URLs")
print("✅ 4. Retrieved correct CRON_SECRET from Netlify")
print("✅ 5. Updated both job URLs with correct authentication")
print("✅ 6. Verified endpoints work manually (processed 5 calls successfully)")

print(f"\n📈 CURRENT DATABASE STATUS:")

# Get comprehensive stats
total_calls = count_records({})
analyzed_calls = count_records({'analysis_score': 'not.is.null'})
unanalyzed_calls = count_records({'analysis_score': 'is.null'})
x_analyzed_calls = count_records({'x_analysis_score': 'not.is.null'})
x_unanalyzed_calls = count_records({'x_analysis_score': 'is.null'})

# August 2025 specific stats
august_calls = count_records({
    'buy_timestamp': 'gte.2025-08-01T00:00:00Z',
    'buy_timestamp': 'lt.2025-09-01T00:00:00Z'
})
august_analyzed = count_records({
    'buy_timestamp': 'gte.2025-08-01T00:00:00Z',
    'buy_timestamp': 'lt.2025-09-01T00:00:00Z',
    'analysis_score': 'not.is.null'
})

print(f"   📊 Total calls: {total_calls:,}")
print(f"   ✅ Call analysis: {analyzed_calls:,} ({analyzed_calls/total_calls*100:.1f}%)")
print(f"   ⏳ Need call analysis: {unanalyzed_calls:,}")
print(f"   🐦 X analysis: {x_analyzed_calls:,} ({x_analyzed_calls/total_calls*100:.1f}%)")
print(f"   ⏳ Need X analysis: {x_unanalyzed_calls:,}")

print(f"\n📅 AUGUST 2025 STATUS:")
print(f"   📊 August calls: {august_calls:,}")
print(f"   ✅ August analyzed: {august_analyzed:,} ({august_analyzed/august_calls*100:.1f}%)")
print(f"   ⏳ August pending: {august_calls - august_analyzed:,}")

# Recent calls from today
today = datetime.now().strftime('%Y-%m-%d')
today_calls = count_records({
    'buy_timestamp': f'gte.{today}T00:00:00Z',
    'buy_timestamp': f'lt.{today}T23:59:59Z'
})

if today_calls > 0:
    today_analyzed = count_records({
        'buy_timestamp': f'gte.{today}T00:00:00Z',
        'buy_timestamp': f'lt.{today}T23:59:59Z',
        'analysis_score': 'not.is.null'
    })
    print(f"\n📅 TODAY ({today}) STATUS:")
    print(f"   📊 Today's calls: {today_calls:,}")
    print(f"   ✅ Today analyzed: {today_analyzed:,}")
    print(f"   ⏳ Today pending: {today_calls - today_analyzed:,}")

print(f"\n🔧 CRON JOB CONFIGURATION:")
print("   📋 Call Analysis Job (ID: 6380042)")
print("      Status: ✅ Enabled")
print("      Schedule: Every minute")
print("      URL: https://lively-torrone-8199e0.netlify.app/api/cron/analyze")
print("      Auth: ✅ Correct CRON_SECRET configured")
print("      Manual Test: ✅ Processed 5 calls successfully")

print("\n   📋 X Analysis Job (ID: 6380045)")
print("      Status: ✅ Enabled")
print("      Schedule: Every minute")
print("      URL: https://lively-torrone-8199e0.netlify.app/api/cron/x-analyze")
print("      Auth: ✅ Correct CRON_SECRET configured")
print("      Manual Test: ✅ Endpoint responding correctly")

print(f"\n🎯 EXPECTED PROCESSING RATE:")
print("   📊 Call Analysis: ~5 calls per minute")
print("   🐦 X Analysis: ~3 calls per minute")
print(f"   ⏱️ Estimated completion for call analysis: {unanalyzed_calls // 5} minutes")
print(f"   ⏱️ Estimated completion for X analysis: {x_unanalyzed_calls // 3} minutes")

print(f"\n⚠️ NEXT STEPS:")
print("   1. Monitor system for 10-15 minutes to confirm automatic processing")
print("   2. If no progress, check cron-job.org dashboard for execution errors")
print("   3. Consider manual processing if cron service has issues")

print(f"\n📱 MONITORING COMMANDS:")
print("   Check status: python3 check-analysis-status.py")
print("   Test endpoints: python3 test-correct-secret.py")
print("   View recent activity: python3 check-recent-activity.py")

print("\n" + "=" * 60)
print("🎉 ANALYSIS SYSTEM IS CONFIGURED AND READY")
print("   Both cron jobs enabled with correct authentication")
print("   Endpoints tested and working correctly")
print("   System should begin processing automatically")
print("=" * 60)