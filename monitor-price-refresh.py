import os
from supabase import create_client
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time

load_dotenv()
url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

print("=== MONITORING PRICE REFRESH PROGRESS ===")

# Initial count
initial_count = supabase.table('crypto_calls').select('id', count='exact').not_.is_('current_price', 'null').not_.is_('contract_address', 'null').lt('price_updated_at', datetime.utcnow() - timedelta(hours=2)).execute()
print(f"Starting count of tokens needing update: {initial_count.count}")

# Check recently updated
recent = supabase.table('crypto_calls').select('ticker, current_price, roi_percent, price_updated_at').not_.is_('current_price', 'null').order('price_updated_at', desc=True).limit(10).execute()

print("\nMost recently updated tokens:")
for token in recent.data[:5]:
    updated_time = datetime.fromisoformat(token['price_updated_at'].replace('Z', '+00:00'))
    minutes_ago = (datetime.utcnow() - updated_time.replace(tzinfo=None)).total_seconds() / 60
    print(f"  {token['ticker']}: ${token['current_price']:.8f} (ROI: {token['roi_percent']:.1f}%) - {minutes_ago:.1f} min ago")

# Monitor progress
print("\nChecking progress every 30 seconds...")
last_count = initial_count.count

for i in range(10):  # Check 10 times
    time.sleep(30)
    current_count = supabase.table('crypto_calls').select('id', count='exact').not_.is_('current_price', 'null').not_.is_('contract_address', 'null').lt('price_updated_at', datetime.utcnow() - timedelta(hours=2)).execute()
    
    tokens_updated = last_count - current_count.count
    rate = tokens_updated * 2  # Per minute
    
    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Remaining: {current_count.count} | Updated in last 30s: {tokens_updated} | Rate: {rate}/min")
    
    if tokens_updated > 0:
        # Show some recently updated
        recent = supabase.table('crypto_calls').select('ticker, roi_percent').not_.is_('current_price', 'null').gte('price_updated_at', (datetime.utcnow() - timedelta(seconds=35)).isoformat()).limit(5).execute()
        if recent.data:
            print("  Recent updates:", ', '.join([f"{t['ticker']} ({t['roi_percent']:.1f}%)" for t in recent.data]))
    
    last_count = current_count.count
    
    if current_count.count == 0:
        print("\n✅ All tokens updated!")
        break