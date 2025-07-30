#!/usr/bin/env python3
import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(url, key)

# Query tokens without prices (both entry and current are NULL)
print("Fetching tokens without any price data...")
response = supabase.table('crypto_calls').select(
    'id, ticker, network, contract_address, created_at, price_at_call, current_price, roi_percent, ath_roi_percent'
).is_('price_at_call', 'null').is_('current_price', 'null').order('created_at', desc=True).limit(100).execute()

tokens_without_prices = response.data

print(f"\nFound {len(tokens_without_prices)} tokens without any prices (showing first 100)")
print("\nFirst 20 tokens without prices:")
print("-" * 100)

for i, token in enumerate(tokens_without_prices[:20]):
    print(f"{i+1}. {token['ticker']} ({token['network']})")
    print(f"   Contract: {token['contract_address']}")
    print(f"   Created: {token['created_at']}")
    print(f"   ROI: {token['roi_percent']}")
    print(f"   ATH ROI: {token['ath_roi_percent']}")
    print()

# Get total count of tokens without prices
count_response = supabase.table('crypto_calls').select('*', count='exact', head=True).is_('price_at_call', 'null').is_('current_price', 'null').execute()
total_without_prices = count_response.count

print(f"\nTotal tokens without prices: {total_without_prices}")

# Check if these tokens have ROI values despite no prices
tokens_with_roi_no_price = [t for t in tokens_without_prices if t['roi_percent'] is not None or t['ath_roi_percent'] is not None]
print(f"\nTokens with ROI but no prices: {len(tokens_with_roi_no_price)}")

# Let's check a specific example in detail
if tokens_without_prices:
    example_token = tokens_without_prices[0]
    print(f"\nDetailed check for {example_token['ticker']}:")
    
    # Get full record
    full_record = supabase.table('crypto_calls').select('*').eq('id', example_token['id']).single().execute()
    
    print(f"price_at_call: {full_record.data.get('price_at_call')}")
    print(f"current_price: {full_record.data.get('current_price')}")
    print(f"price_current: {full_record.data.get('price_current')}")  # Check alternative column
    print(f"price_updated_at: {full_record.data.get('price_updated_at')}")
    print(f"price_fetched_at: {full_record.data.get('price_fetched_at')}")
    print(f"roi_percent: {full_record.data.get('roi_percent')}")
    print(f"ath_roi_percent: {full_record.data.get('ath_roi_percent')}")

# Check why ROI sorting might show these first
print("\n\nChecking ROI sorting behavior...")
# When sorting by ROI descending, NULL values might appear first or last depending on DB
null_roi_tokens = supabase.table('crypto_calls').select(
    'ticker, network, roi_percent, ath_roi_percent, price_at_call, current_price'
).is_('roi_percent', 'null').limit(10).execute()

print(f"\nTokens with NULL roi_percent: {len(null_roi_tokens.data)}")

# Now check tokens ordered by roi_percent DESC
high_roi_tokens = supabase.table('crypto_calls').select(
    'ticker, network, roi_percent, ath_roi_percent, price_at_call, current_price'
).order('roi_percent', desc=True).limit(20).execute()

print("\nTop 20 tokens by ROI (descending):")
for i, token in enumerate(high_roi_tokens.data):
    print(f"{i+1}. {token['ticker']} - ROI: {token['roi_percent']}%, ATH ROI: {token['ath_roi_percent']}%")