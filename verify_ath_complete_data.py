import os
from supabase import create_client, Client

# Get credentials from environment
supabase_url = os.environ.get('SUPABASE_URL', 'https://eucfoommxxvqmmwdbkdv.supabase.co')
supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Ria2R2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzU2Mjg4MSwiZXhwIjoyMDYzMTM4ODgxfQ.VcC7Bp3zMFYor3eVDonoG7BuS7AavemQnSOhrWcY5Y4')

# Create client
supabase: Client = create_client(supabase_url, supabase_key)

# Query for recent tokens with complete ATH data
response = supabase.table('crypto_calls').select(
    'id, ticker, network, contract_address, price_at_call, ath_price, ath_timestamp, ath_roi_percent, buy_timestamp'
).not_.is_('ath_price', 'null').not_.is_('price_at_call', 'null').not_.is_('ath_roi_percent', 'null').order('ath_timestamp', desc=True).limit(20).execute()

print('Recent tokens with COMPLETE ATH data:')
print('=' * 100)
for i, token in enumerate(response.data, 1):
    print(f'{i}. {token["ticker"]} ({token["network"]})')
    print(f'   Contract: {token["contract_address"]}')
    print(f'   Price at call: ${token["price_at_call"]}')
    print(f'   ATH price: ${token["ath_price"]}')
    print(f'   ATH ROI: {token["ath_roi_percent"]}%')
    print(f'   ATH timestamp: {token["ath_timestamp"]}')
    print(f'   Buy timestamp: {token["buy_timestamp"]}')
    print()

# Get count of tokens by network
print('\nTokens by network:')
print('=' * 50)
for network in ['ethereum', 'solana', 'base', 'bsc']:
    count_response = supabase.table('crypto_calls').select('id', count='exact').not_.is_('ath_price', 'null').not_.is_('price_at_call', 'null').not_.is_('ath_roi_percent', 'null').eq('network', network).execute()
    print(f'{network}: {count_response.count} tokens with complete ATH data')