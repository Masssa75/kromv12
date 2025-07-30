import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

print('=== PRICE UPDATE DISTRIBUTION ===')

# Get recent updates
now = datetime.utcnow()
last_3_hours = (now - timedelta(hours=3)).isoformat()
last_12_hours = (now - timedelta(hours=12)).isoformat()
last_24_hours = (now - timedelta(hours=24)).isoformat()

# Count recent updates
recent_3h = supabase.table('crypto_calls').select('count', count='exact').gte('price_updated_at', last_3_hours).execute()
recent_12h = supabase.table('crypto_calls').select('count', count='exact').gte('price_updated_at', last_12_hours).execute()
recent_24h = supabase.table('crypto_calls').select('count', count='exact').gte('price_updated_at', last_24_hours).execute()

print(f'\nPrices updated in:')
print(f'  Last 3 hours: {recent_3h.count:,} tokens (likely from refresh-prices)')
print(f'  Last 12 hours: {recent_12h.count:,} tokens')
print(f'  Last 24 hours: {recent_24h.count:,} tokens')

# Check accuracy of recently refreshed prices
print('\n=== CHECKING RECENTLY REFRESHED PRICES ===')
recent = supabase.table('crypto_calls').select('ticker, current_price, roi_percent, price_updated_at').gte('price_updated_at', last_3_hours).limit(10).execute()

print(f'\nSample of tokens refreshed in last 3 hours:')
for token in recent.data[:5]:
    print(f"  {token['ticker']}: ${token['current_price']} ({token['roi_percent']:.1f}% ROI)")

# Check page 9 tokens (assuming 20 per page, so offset 160)
print('\n=== CHECKING PAGE 9 TOKENS ===')
page_9 = supabase.table('crypto_calls').select('ticker, current_price, roi_percent, price_updated_at').not_.is_('current_price', 'null').order('created_at', desc=True).offset(160).limit(20).execute()

print(f'\nTokens on page 9:')
for i, token in enumerate(page_9.data[:10]):
    updated = datetime.fromisoformat(token['price_updated_at'].replace('+00:00', ''))
    hours_ago = (now - updated).total_seconds() / 3600
    print(f"  {token['ticker']}: ${token['current_price']} ({token['roi_percent']:.1f}% ROI) - Updated {hours_ago:.1f}h ago")
