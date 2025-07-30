import os
from supabase import create_client, Client

# Get credentials from environment
supabase_url = os.environ.get('SUPABASE_URL', 'https://eucfoommxxvqmmwdbkdv.supabase.co')
supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Ria2R2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzU2Mjg4MSwiZXhwIjoyMDYzMTM4ODgxfQ.VcC7Bp3zMFYor3eVDonoG7BuS7AavemQnSOhrWcY5Y4')

# Create client
supabase: Client = create_client(supabase_url, supabase_key)

# Get tokens to verify (mix of networks, with complete data and pool addresses)
test_tokens = [
    # High ROI tokens
    {'ticker': 'ORB', 'network': 'bsc', 'expected_roi': 14318.33609930758},
    {'ticker': 'NOVAQ', 'network': 'ethereum', 'expected_roi': 905.5172759480939},
    
    # Medium ROI tokens  
    {'ticker': 'TOR', 'network': 'ethereum', 'expected_roi': 234.06083620258204},
    {'ticker': 'CMD', 'network': 'solana', 'expected_roi': 220.07400155734143},
    {'ticker': 'PEPEV2', 'network': 'ethereum', 'expected_roi': 152.26474197345578},
    
    # Low ROI tokens
    {'ticker': 'FACELESS', 'network': 'solana', 'expected_roi': 55.13185497767061},
    {'ticker': 'VITALIKSAMA', 'network': 'ethereum', 'expected_roi': 27.82082942518922},
    {'ticker': 'YLT', 'network': 'solana', 'expected_roi': 22.29198939081671},
    
    # Zero ROI tokens
    {'ticker': 'CHAD', 'network': 'ethereum', 'expected_roi': 0},
    {'ticker': 'OCCUPY', 'network': 'solana', 'expected_roi': 0},
]

print('Tokens selected for verification:')
print('=' * 100)

verified_tokens = []
for test in test_tokens:
    # Query for the specific token
    response = supabase.table('crypto_calls').select(
        'id, ticker, network, contract_address, price_at_call, ath_price, ath_timestamp, ath_roi_percent, buy_timestamp, pool_address'
    ).eq('ticker', test['ticker']).eq('network', test['network']).not_.is_('ath_price', 'null').not_.is_('price_at_call', 'null').not_.is_('ath_roi_percent', 'null').limit(1).execute()
    
    if response.data:
        token = response.data[0]
        print(f'\n{token["ticker"]} ({token["network"]}):')
        print(f'  Contract: {token["contract_address"]}')
        print(f'  Pool: {token["pool_address"]}')
        print(f'  Price at call: ${token["price_at_call"]}')
        print(f'  ATH price: ${token["ath_price"]}')
        print(f'  ATH ROI: {token["ath_roi_percent"]}% (expected: {test["expected_roi"]}%)')
        print(f'  ATH timestamp: {token["ath_timestamp"]}')
        print(f'  Buy timestamp: {token["buy_timestamp"]}')
        
        if token["pool_address"]:
            verified_tokens.append(token)

print(f'\n\nFound {len(verified_tokens)} tokens with pool addresses for verification')