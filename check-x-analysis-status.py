#\!/usr/bin/env python3
"""Check X analysis status and progress"""

import os
import requests
from datetime import datetime, timezone

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

print('X ANALYSIS STATUS CHECK')
print('=' * 50)

# 1. Count calls that need X analysis
headers_with_count = {**headers, 'Prefer': 'count=exact'}
response = requests.get(
    f'{url}/rest/v1/crypto_calls',
    headers=headers_with_count,
    params={
        'select': 'count',
        'x_raw_tweets': 'not.is.null',
        'x_analysis_score': 'is.null'
    }
)
needs_x_analysis = int(response.headers.get('content-range', '0/0').split('/')[1])
print(f'Calls with tweets that need X analysis: {needs_x_analysis}')

# 2. Count calls with completed X analysis
response = requests.get(
    f'{url}/rest/v1/crypto_calls',
    headers=headers_with_count,
    params={
        'select': 'count',
        'x_analysis_score': 'not.is.null'
    }
)
has_x_analysis = int(response.headers.get('content-range', '0/0').split('/')[1])
print(f'Calls with completed X analysis: {has_x_analysis}')

# 3. Count total calls with tweets
response = requests.get(
    f'{url}/rest/v1/crypto_calls',
    headers=headers_with_count,
    params={
        'select': 'count',
        'x_raw_tweets': 'not.is.null'
    }
)
total_with_tweets = int(response.headers.get('content-range', '0/0').split('/')[1])
print(f'Total calls with tweet data: {total_with_tweets}')
if total_with_tweets > 0:
    progress = (has_x_analysis / total_with_tweets) * 100
    print(f'X analysis progress: {progress:.1f}% complete')

# 4. Check most recent X analysis
print(f'\nMost recent X analyses:')
response = requests.get(
    f'{url}/rest/v1/crypto_calls',
    headers=headers,
    params={
        'select': 'ticker,x_analyzed_at,x_analysis_score',
        'x_analyzed_at': 'not.is.null',
        'order': 'x_analyzed_at.desc',
        'limit': '5'
    }
)
recent_x = response.json()
now = datetime.now(timezone.utc)
for call in recent_x:
    analyzed_at = datetime.fromisoformat(call['x_analyzed_at'].replace('Z', '+00:00'))
    time_ago = (now - analyzed_at).total_seconds() / 3600
    print(f'  {call["ticker"]:10} - Score: {call["x_analysis_score"]} - {time_ago:.1f} hours ago')

# 5. Check if any X analysis happened in last hour
one_hour_ago = (datetime.now(timezone.utc) - datetime.timedelta(hours=1)).isoformat()
response = requests.get(
    f'{url}/rest/v1/crypto_calls',
    headers=headers_with_count,
    params={
        'select': 'count',
        'x_analyzed_at': f'gte.{one_hour_ago}'
    }
)
recent_count = int(response.headers.get('content-range', '0/0').split('/')[1])
print(f'\nX analyses completed in last hour: {recent_count}')

# 6. Check the oldest unanalyzed call with tweets
print(f'\nOldest calls with tweets waiting for X analysis:')
response = requests.get(
    f'{url}/rest/v1/crypto_calls',
    headers=headers,
    params={
        'select': 'ticker,created_at',
        'x_raw_tweets': 'not.is.null',
        'x_analysis_score': 'is.null',
        'order': 'created_at.asc',
        'limit': '5'
    }
)
oldest_waiting = response.json()
for call in oldest_waiting:
    created_at = datetime.fromisoformat(call['created_at'].replace('Z', '+00:00'))
    days_ago = (now - created_at).days
    print(f'  {call["ticker"]:10} - Waiting {days_ago} days')
