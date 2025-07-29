import os
from datetime import datetime, timedelta
from supabase import create_client

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

supabase = create_client(url, key)

# Get the 30 newest calls
response = supabase.table('crypto_calls').select(
    'id, ticker, created_at, buy_timestamp, analysis_score, analyzed_at, x_analysis_score, x_analyzed_at, krom_id'
).order('created_at', desc=True).limit(30).execute()

print('\n=== 30 NEWEST CALLS IN DATABASE ===\n')
print(f"{'Created At':<20} {'Ticker':<10} {'Analysis':<10} {'X Analysis':<12} {'KROM ID':<15}")
print('-' * 80)

for call in response.data:
    created = call['created_at'][:19] if call['created_at'] else 'N/A'
    ticker = call['ticker'] or 'UNKNOWN'
    analysis = f"{call['analysis_score'] or '-'}" + (' ✓' if call['analyzed_at'] else '')
    x_analysis = f"{call['x_analysis_score'] or '-'}" + (' ✓' if call['x_analyzed_at'] else '')
    krom_id = call['krom_id'] or 'N/A'
    
    print(f'{created:<20} {ticker:<10} {analysis:<10} {x_analysis:<12} {krom_id:<15}')

# Check if there are any calls created in the last hour
one_hour_ago = (datetime.utcnow() - timedelta(hours=1)).isoformat()
recent_response = supabase.table('crypto_calls').select('count', count='exact').gte('created_at', one_hour_ago).execute()

print(f'\nCalls created in last hour: {recent_response.count}')

# Check the oldest unanalyzed call
unanalyzed = supabase.table('crypto_calls').select(
    'created_at, ticker, krom_id'
).is_('analysis_score', 'null').order('created_at').limit(5).execute()

if unanalyzed.data:
    print(f'\nOldest 5 unanalyzed calls:')
    for call in unanalyzed.data:
        print(f"  {call['ticker']} (ID: {call['krom_id']}) from {call['created_at'][:19]}")

# Check for calls without X analysis but with tweets
no_x_analysis = supabase.table('crypto_calls').select(
    'created_at, ticker, krom_id'
).is_('x_analysis_score', 'null').not_('x_raw_tweets', 'is', 'null').order('created_at').limit(5).execute()

if no_x_analysis.data:
    print(f'\nOldest 5 calls with tweets but no X analysis:')
    for call in no_x_analysis.data:
        print(f"  {call['ticker']} (ID: {call['krom_id']}) from {call['created_at'][:19]}")