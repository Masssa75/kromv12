from supabase import create_client

supabase = create_client(
    'https://eucfoommxxvqmmwdbkdv.supabase.co', 
    'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Ria2R2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzU2Mjg4MSwiZXhwIjoyMDYzMTM4ODgxfQ.VcC7Bp3zMFYor3eVDonoG7BuS7AavemQnSOhrWcY5Y4'
)

# Check ATH count
response = supabase.table('crypto_calls').select('id', count='exact').not_.is_('ath_price', 'null').execute()
print(f'Total tokens with ATH data: {response.count}')

# Check BONKGIRL specifically
bonkgirl = supabase.table('crypto_calls').select('ticker, ath_price, ath_timestamp, ath_roi_percent').eq('ticker', 'BONKGIRL').execute()
print(f'\nBONKGIRL records found: {len(bonkgirl.data)}')
for r in bonkgirl.data:
    print(f'  ATH price: {r["ath_price"]}')
    print(f'  ATH timestamp: {r["ath_timestamp"]}')
    print(f'  ATH ROI: {r["ath_roi_percent"]}%')