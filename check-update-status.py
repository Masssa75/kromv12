import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

# Get current status
old_count = supabase.table('crypto_calls').select('id', count='exact').not_.is_('current_price', 'null').not_.is_('contract_address', 'null').lt('price_updated_at', datetime.utcnow() - timedelta(hours=2)).execute()
total_with_price = supabase.table('crypto_calls').select('id', count='exact').not_.is_('current_price', 'null').execute()

print('=== CURRENT STATUS ===')
print(f'Total tokens with prices: {total_with_price.count}')
print(f'Tokens needing update (>2 hours old): {old_count.count}')
print(f'Recently updated (within 2 hours): {total_with_price.count - old_count.count}')
print(f'Progress: {((4488 - old_count.count) / 4488 * 100):.1f}% complete')

# Check if updates are happening
recent = supabase.table('crypto_calls').select('ticker, current_price, roi_percent, price_updated_at').not_.is_('price_updated_at', 'null').order('price_updated_at', desc=True).limit(10).execute()
print('\nMost recent updates:')
for token in recent.data:
    timestamp = token['price_updated_at'][:19] if token['price_updated_at'] else 'Unknown'
    roi = f"{token['roi_percent']:.1f}%" if token['roi_percent'] is not None else 'N/A'
    print(f"  {token['ticker']}: ${token['current_price']:.8f} (ROI: {roi}) - {timestamp}")

# Check rate
one_min_ago = (datetime.utcnow() - timedelta(minutes=1)).isoformat()
recent_count = supabase.table('crypto_calls').select('id', count='exact').gte('price_updated_at', one_min_ago).execute()
print(f'\nTokens updated in last minute: {recent_count.count}')