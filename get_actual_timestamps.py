import os
from supabase import create_client, Client
from datetime import datetime

# Get credentials from environment
supabase_url = os.environ.get('SUPABASE_URL', 'https://eucfoommxxvqmmwdbkdv.supabase.co')
supabase_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Ria2R2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzU2Mjg4MSwiZXhwIjoyMDYzMTM4ODgxfQ.VcC7Bp3zMFYor3eVDonoG7BuS7AavemQnSOhrWcY5Y4')

# Create client
supabase: Client = create_client(supabase_url, supabase_key)

# Get tokens with actual timestamps
tokens = [
    {'ticker': 'ORB', 'network': 'bsc', 'pool': '0x3d7B64Fdf42eD266DB70047567fBd209FB7Ce151'},
    {'ticker': 'NOVAQ', 'network': 'ethereum', 'pool': '0x462A1e822bd97dCF65202c157479b23b5CF0a323'},
    {'ticker': 'TOR', 'network': 'ethereum', 'pool': '0x8c05830A9549A3bfe85F18FE2453FE3162445A8D'},
    {'ticker': 'CMD', 'network': 'solana', 'pool': '8kaEhweQhLXQ2bbCaUbcmAW54ozwgTR1SxCrVWqSFjB9'},
    {'ticker': 'FACELESS', 'network': 'solana', 'pool': '8XpuQ3HQesVTp5DBYSRuPBTBS5HxuzGERBDoLL9swsLj'},
    {'ticker': 'VITALIKSAMA', 'network': 'ethereum', 'pool': '0xb2052714D81d63DE122b61f99552e7d4833A8f27'},
    {'ticker': 'YLT', 'network': 'solana', 'pool': 'EckoPfSc4XcBockkqJ5XkbBdgoa6hUnCauhu7J3baWsR'},
    {'ticker': 'CHAD', 'network': 'ethereum', 'pool': '0xd20fd859A32306C0b77d9A16501B23EB6C18057F'},
    {'ticker': 'OCCUPY', 'network': 'solana', 'pool': 'DFHADernc2HtQbnPGmk3BEMbt5kU7hnn6TSNcSHyv1M1'}
]

print('Getting actual timestamps from database:')
print('=' * 80)

for token in tokens:
    response = supabase.table('crypto_calls').select(
        'ticker, network, buy_timestamp, created_at, price_at_call, ath_price, ath_roi_percent, raw_data'
    ).eq('ticker', token['ticker']).eq('network', token['network']).eq('pool_address', token['pool']).not_.is_('ath_price', 'null').limit(1).execute()
    
    if response.data:
        data = response.data[0]
        print(f"\n{data['ticker']} ({data['network']}):")
        print(f"  Buy timestamp: {data['buy_timestamp']}")
        print(f"  Created at: {data['created_at']}")
        
        # Extract timestamp from raw_data if buy_timestamp is None
        if not data['buy_timestamp'] and data['raw_data']:
            raw_data = data['raw_data']
            if 'datetime' in raw_data:
                raw_dt = raw_data['datetime']
                print(f"  Raw data datetime: {raw_dt}")
                # Convert to timestamp
                try:
                    dt = datetime.fromisoformat(raw_dt.replace('Z', '+00:00'))
                    timestamp = int(dt.timestamp())
                    print(f"  Converted timestamp: {timestamp}")
                    print(f"  Human readable: {dt.strftime('%Y-%m-%d %H:%M:%S UTC')}")
                except:
                    print("  Failed to parse datetime")
        
        print(f"  Price at call: ${data['price_at_call']}")
        print(f"  ATH price: ${data['ath_price']}")
        print(f"  ATH ROI: {data['ath_roi_percent']}%")