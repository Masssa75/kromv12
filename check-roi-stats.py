import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

# Get tokens with high but not astronomical ROI
result = supabase.table('crypto_calls').select(
    'ticker, roi_percent'
).not_.is_('roi_percent', 'null').gte('roi_percent', 1000).lt('roi_percent', 10000).order('roi_percent', desc=True).limit(10).execute()

print('Tokens with 1,000% - 10,000% ROI:')
for token in result.data:
    print(f"  {token['ticker']}: {token['roi_percent']:.0f}%")

# Check overall stats
stats = supabase.table('crypto_calls').select('roi_percent').not_.is_('roi_percent', 'null').execute()
rois = [t['roi_percent'] for t in stats.data]
print(f'\nROI Statistics:')
print(f'  Total tokens with ROI: {len(rois)}')
print(f'  ROI > 1000%: {len([r for r in rois if r > 1000])}')
print(f'  ROI > 100%: {len([r for r in rois if r > 100])}')
print(f'  ROI between -50% and 100%: {len([r for r in rois if -50 <= r <= 100])}')
print(f'  ROI < -90%: {len([r for r in rois if r < -90])}')