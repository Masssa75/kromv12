import os
from supabase import create_client, Client
from datetime import datetime, timedelta

# Get credentials from environment
supabase_url = os.environ.get('SUPABASE_URL', 'https://eucfoommxxvqmmwdbkdv.supabase.co')
supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Ria2R2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzU2Mjg4MSwiZXhwIjoyMDYzMTM4ODgxfQ.VcC7Bp3zMFYor3eVDonoG7BuS7AavemQnSOhrWcY5Y4')

# Create client
supabase: Client = create_client(supabase_url, supabase_key)

print('ATH Processing Progress Check')
print('=' * 80)

# Get total count of tokens
total_response = supabase.table('crypto_calls').select('id', count='exact').execute()
total_count = total_response.count

# Get count of tokens with ATH data
ath_response = supabase.table('crypto_calls').select('id', count='exact').not_.is_('ath_price', 'null').execute()
ath_count = ath_response.count

# Get count of recently processed ATH (last hour)
one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
recent_ath_response = supabase.table('crypto_calls').select('id', count='exact').not_.is_('ath_price', 'null').gte('ath_timestamp', one_hour_ago).execute()
recent_ath_count = recent_ath_response.count

# Get some recent ATH entries
recent_entries = supabase.table('crypto_calls').select(
    'ticker, network, ath_price, ath_timestamp, ath_roi_percent'
).not_.is_('ath_price', 'null').order('ath_timestamp', desc=True).limit(10).execute()

print(f'Total tokens in database: {total_count:,}')
print(f'Tokens with ATH data: {ath_count:,} ({ath_count/total_count*100:.1f}%)')
print(f'ATH processed in last hour: {recent_ath_count}')
print(f'Tokens still need ATH: {total_count - ath_count:,}')

print('\nMost recently processed ATH entries:')
print('-' * 80)
for token in recent_entries.data:
    print(f"{token['ticker']} ({token['network']}) - ATH: ${token['ath_price']} - ROI: {token['ath_roi_percent']}% - {token['ath_timestamp']}")

# Check if edge function is running
print('\n\nChecking for any error patterns in recent entries...')
error_tokens = supabase.table('crypto_calls').select(
    'ticker, network, ath_price, price_at_call'
).not_.is_('ath_price', 'null').is_('ath_roi_percent', 'null').limit(20).execute()

if error_tokens.data:
    print(f'\nFound {len(error_tokens.data)} tokens with ATH price but no ROI calculated:')
    for token in error_tokens.data[:5]:
        print(f"  {token['ticker']} ({token['network']}) - ATH: ${token['ath_price']} - Price at call: ${token['price_at_call']}")

# Check for tokens with price_at_call but no ATH yet
no_ath_with_price = supabase.table('crypto_calls').select(
    'ticker, network, price_at_call, created_at'
).is_('ath_price', 'null').not_.is_('price_at_call', 'null').order('created_at', desc=False).limit(10).execute()

print(f'\n\nOldest tokens with price but no ATH:')
for token in no_ath_with_price.data:
    print(f"  {token['ticker']} ({token['network']}) - Price: ${token['price_at_call']} - Created: {token['created_at']}")