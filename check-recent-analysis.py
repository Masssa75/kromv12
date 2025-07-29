#!/usr/bin/env python3
"""Check if any analysis has been processed recently"""

import os
import requests
from datetime import datetime, timezone, timedelta

# Load environment variables
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

if not url or not key:
    with open('.env', 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                k, v = line.strip().split('=', 1)
                if k == 'SUPABASE_URL' and not url:
                    url = v.strip().strip('"')
                elif k == 'SUPABASE_SERVICE_ROLE_KEY' and not key:
                    key = v.strip().strip('"')

headers = {
    'apikey': key,
    'Authorization': f'Bearer {key}',
    'Content-Type': 'application/json'
}

print('CHECKING RECENT ANALYSIS PROGRESS')
print('=' * 45)

# Check recent call analyses (last 10 minutes)
ten_min_ago = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat() + 'Z'
print(f'Looking for analyses since: {ten_min_ago}')

# Recent call analyses
response = requests.get(
    f'{url}/rest/v1/crypto_calls',
    headers=headers,
    params={
        'select': 'ticker,analyzed_at,analysis_score,analysis_model',
        'analyzed_at': f'gte.{ten_min_ago}',
        'analysis_score': 'not.is.null',
        'order': 'analyzed_at.desc',
        'limit': '10'
    }
)

recent_call_analyses = response.json()
print(f'\nRecent CALL analyses ({len(recent_call_analyses)} found):')
for analysis in recent_call_analyses:
    analyzed_time = datetime.fromisoformat(analysis['analyzed_at'].replace('Z', '+00:00'))
    minutes_ago = (datetime.now(timezone.utc) - analyzed_time).total_seconds() / 60
    print(f'  {analysis["ticker"]:10} - Score: {analysis["analysis_score"]} - Model: {analysis.get("analysis_model", "Unknown")} - {minutes_ago:.1f}min ago')

# Recent X analyses
response = requests.get(
    f'{url}/rest/v1/crypto_calls',
    headers=headers,
    params={
        'select': 'ticker,x_analyzed_at,x_analysis_score,x_analysis_model',
        'x_analyzed_at': f'gte.{ten_min_ago}',
        'x_analysis_score': 'not.is.null',
        'order': 'x_analyzed_at.desc',
        'limit': '10'
    }
)

recent_x_analyses = response.json()
print(f'\nRecent X analyses ({len(recent_x_analyses)} found):')
for analysis in recent_x_analyses:
    analyzed_time = datetime.fromisoformat(analysis['x_analyzed_at'].replace('Z', '+00:00'))
    minutes_ago = (datetime.now(timezone.utc) - analyzed_time).total_seconds() / 60
    print(f'  {analysis["ticker"]:10} - Score: {analysis["x_analysis_score"]} - Model: {analysis.get("x_analysis_model", "Unknown")} - {minutes_ago:.1f}min ago')

# Current remaining counts
headers_count = {**headers, 'Prefer': 'count=exact'}

response = requests.get(f'{url}/rest/v1/crypto_calls', headers=headers_count, params={'select': 'count', 'analysis_score': 'is.null'})
need_call = int(response.headers.get('content-range', '0/0').split('/')[1])

response = requests.get(f'{url}/rest/v1/crypto_calls', headers=headers_count, params={'select': 'count', 'x_raw_tweets': 'not.is.null', 'x_analysis_score': 'is.null'})
need_x = int(response.headers.get('content-range', '0/0').split('/')[1])

print(f'\nCURRENT STATUS:')
print(f'  Still need call analysis: {need_call}')
print(f'  Still need X analysis: {need_x}')

# Check if AIR token has been reprocessed
print(f'\nChecking AIR token status:')
response = requests.get(
    f'{url}/rest/v1/crypto_calls',
    headers=headers,
    params={
        'select': 'ticker,analysis_score,analysis_reasoning,x_analysis_score,x_analysis_reasoning',
        'ticker': 'eq.AIR',
        'limit': '1'
    }
)
air_token = response.json()
if air_token:
    air = air_token[0]
    call_status = 'PROCESSED' if air.get('analysis_score') else 'PENDING'
    x_status = 'PROCESSED' if air.get('x_analysis_score') else 'PENDING'
    print(f'  Call analysis: {call_status}')
    print(f'  X analysis: {x_status}')
    if air.get('analysis_reasoning'):
        print(f'  Has real reasoning: YES')
    else:
        print(f'  Has real reasoning: NO')