import os
import requests
from datetime import datetime, timedelta

# Get Supabase credentials
url = os.environ.get('NEXT_PUBLIC_SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')

if not url or not key:
    # Try loading from .env file
    with open('.env', 'r') as f:
        for line in f:
            if '=' in line and not line.strip().startswith('#'):
                k, v = line.strip().split('=', 1)
                if k == 'NEXT_PUBLIC_SUPABASE_URL' and not url:
                    url = v.strip().strip('"')
                elif k == 'SUPABASE_SERVICE_ROLE_KEY' and not key:
                    key = v.strip().strip('"')

# Headers for Supabase
headers = {
    'apikey': key,
    'Authorization': f'Bearer {key}',
    'Content-Type': 'application/json'
}

# Get the 30 newest calls
response = requests.get(
    f"{url}/rest/v1/crypto_calls",
    headers=headers,
    params={
        'select': 'id,ticker,created_at,buy_timestamp,analysis_score,analyzed_at,x_analysis_score,x_analyzed_at,krom_id',
        'order': 'created_at.desc',
        'limit': '30'
    }
)

calls = response.json()

print('\n=== 30 NEWEST CALLS IN DATABASE ===\n')
print(f"{'Created At':<20} {'Ticker':<10} {'Analysis':<10} {'X Analysis':<12} {'KROM ID':<15}")
print('-' * 80)

for call in calls:
    created = call['created_at'][:19] if call['created_at'] else 'N/A'
    ticker = call['ticker'] or 'UNKNOWN'
    analysis = f"{call['analysis_score'] or '-'}" + (' ✓' if call['analyzed_at'] else '')
    x_analysis = f"{call['x_analysis_score'] or '-'}" + (' ✓' if call['x_analyzed_at'] else '')
    krom_id = call['krom_id'] or 'N/A'
    
    print(f'{created:<20} {ticker:<10} {analysis:<10} {x_analysis:<12} {krom_id:<15}')

# Check if there are any calls created in the last hour
one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()
recent_response = requests.get(
    f"{url}/rest/v1/crypto_calls",
    headers=headers,
    params={
        'select': 'id',
        'created_at': f'gte.{one_hour_ago}',
        'limit': '1000'
    }
)
recent_count = len(recent_response.json())

print(f'\nCalls created in last hour: {recent_count}')

# Check the oldest unanalyzed call
unanalyzed_response = requests.get(
    f"{url}/rest/v1/crypto_calls",
    headers=headers,
    params={
        'select': 'created_at,ticker,krom_id',
        'analysis_score': 'is.null',
        'order': 'created_at',
        'limit': '5'
    }
)
unanalyzed = unanalyzed_response.json()

if unanalyzed:
    print(f'\nOldest 5 unanalyzed calls:')
    for call in unanalyzed:
        print(f"  {call['ticker']} (ID: {call['krom_id']}) from {call['created_at'][:19]}")

# Count total unanalyzed
total_unanalyzed_response = requests.get(
    f"{url}/rest/v1/crypto_calls",
    headers=headers,
    params={
        'select': 'id',
        'analysis_score': 'is.null',
        'limit': '1000'
    }
)
total_unanalyzed = len(total_unanalyzed_response.json())
print(f'\nTotal unanalyzed calls: {total_unanalyzed}')