import os
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime, timedelta

load_dotenv()

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

print("=== ANALYZING PRICE UPDATE PATTERNS ===")
print("Looking for when prices were updated...\n")

# Get tokens updated in different time periods
now = datetime.utcnow()
one_hour_ago = now - timedelta(hours=1)
six_hours_ago = now - timedelta(hours=6)
twelve_hours_ago = now - timedelta(hours=12)
twenty_four_hours_ago = now - timedelta(hours=24)

# Count updates by time period
print("Price updates by time period:")

# Last hour (likely from refresh-prices)
last_hour = supabase.table('crypto_calls').select('count', count='exact').not_.is_('current_price', 'null').gte('price_updated_at', one_hour_ago.isoformat()).execute()
print(f"  Last 1 hour: {last_hour.count} tokens")

# 1-6 hours ago
one_to_six = supabase.table('crypto_calls').select('count', count='exact').not_.is_('current_price', 'null').lt('price_updated_at', one_hour_ago.isoformat()).gte('price_updated_at', six_hours_ago.isoformat()).execute()
print(f"  1-6 hours ago: {one_to_six.count} tokens")

# 6-12 hours ago  
six_to_twelve = supabase.table('crypto_calls').select('count', count='exact').not_.is_('current_price', 'null').lt('price_updated_at', six_hours_ago.isoformat()).gte('price_updated_at', twelve_hours_ago.isoformat()).execute()
print(f"  6-12 hours ago: {six_to_twelve.count} tokens")

# 12-24 hours ago
twelve_to_twenty_four = supabase.table('crypto_calls').select('count', count='exact').not_.is_('current_price', 'null').lt('price_updated_at', twelve_hours_ago.isoformat()).gte('price_updated_at', twenty_four_hours_ago.isoformat()).execute()
print(f"  12-24 hours ago: {twelve_to_twenty_four.count} tokens")

# More than 24 hours ago
older = supabase.table('crypto_calls').select('count', count='exact').not_.is_('current_price', 'null').lt('price_updated_at', twenty_four_hours_ago.isoformat()).execute()
print(f"  Older than 24 hours: {older.count} tokens")

print("\n=== CHECKING VERY HIGH ROI TOKENS ===")
print("These might have wrong prices...\n")

# Get tokens with extremely high ROI
high_roi = supabase.table('crypto_calls').select('ticker, contract_address, price_at_call, current_price, roi_percent, price_updated_at').gt('roi_percent', 1000).not_.is_('contract_address', 'null').order('roi_percent', desc=True).limit(10).execute()

for token in high_roi.data:
    update_time = datetime.fromisoformat(token['price_updated_at'].replace('+00:00', ''))
    hours_ago = (now - update_time).total_seconds() / 3600
    
    print(f"{token['ticker']}: +{token['roi_percent']:.0f}% ROI")
    print(f"  Entry: ${token['price_at_call']}")
    print(f"  Current: ${token['current_price']}")
    print(f"  Updated: {hours_ago:.1f} hours ago")
    print(f"  Contract: {token['contract_address'][:20]}...")
    print()

print("\n=== CHECKING BATCH VS REFRESH ACCURACY ===")

# Sample tokens updated >6 hours ago (likely batch)
batch_sample = supabase.table('crypto_calls').select('ticker, contract_address, current_price, roi_percent').not_.is_('current_price', 'null').not_.is_('contract_address', 'null').lt('price_updated_at', six_hours_ago.isoformat()).limit(5).execute()

# Sample tokens updated <1 hour ago (likely refresh)
refresh_sample = supabase.table('crypto_calls').select('ticker, contract_address, current_price, roi_percent').not_.is_('current_price', 'null').not_.is_('contract_address', 'null').gte('price_updated_at', one_hour_ago.isoformat()).limit(5).execute()

print("Batch-updated tokens (>6 hours ago):")
for t in batch_sample.data:
    print(f"  {t['ticker']}: ${t['current_price']} ({t['roi_percent']:.1f}% ROI)")

print("\nRefresh-updated tokens (<1 hour ago):")
for t in refresh_sample.data:
    print(f"  {t['ticker']}: ${t['current_price']} ({t['roi_percent']:.1f}% ROI)")
