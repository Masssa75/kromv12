import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(url, key)

# Get examples of tokens with both prices but no ROI
print("=== EXAMPLES: Tokens with both prices but NO ROI ===\n")

examples = supabase.table("crypto_calls").select("ticker, price_at_call, current_price, roi_percent, price_updated_at").not_.is_("price_at_call", "null").not_.is_("current_price", "null").is_("roi_percent", "null").limit(10).execute()

for token in examples.data:
    expected_roi = ((token["current_price"] - token["price_at_call"]) / token["price_at_call"]) * 100
    print(f"{token['ticker']}:")
    print(f"  Entry: ${token['price_at_call']}")
    print(f"  Now: ${token['current_price']}")
    print(f"  Expected ROI: {expected_roi:.1f}%")
    print(f"  Actual ROI: {token['roi_percent']}")
    print(f"  Price Updated: {token['price_updated_at']}")
    print()

# Check when these prices were updated
print("\n=== PRICE UPDATE TIMELINE ===\n")

# Check tokens updated in last 24 hours
from datetime import datetime, timedelta
now = datetime.utcnow()
yesterday = now - timedelta(hours=24)

recent_updates = supabase.table("crypto_calls").select("count", count="exact").not_.is_("price_at_call", "null").not_.is_("current_price", "null").is_("roi_percent", "null").gte("price_updated_at", yesterday.isoformat()).execute()

print(f"Tokens with both prices but no ROI updated in last 24 hours: {recent_updates.count}")

# Check tokens that DO have ROI
print("\n=== TOKENS WITH ROI ===\n")

with_roi = supabase.table("crypto_calls").select("ticker, price_at_call, current_price, roi_percent, price_updated_at").not_.is_("roi_percent", "null").limit(5).execute()

for token in with_roi.data:
    print(f"{token['ticker']}: ROI = {token['roi_percent']:.1f}%")
    print(f"  Entry: ${token['price_at_call']}")
    print(f"  Now: ${token['current_price']}")
    print(f"  Price Updated: {token['price_updated_at']}")
    print()
