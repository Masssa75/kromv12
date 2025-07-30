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

# Let's check a few of these tokens in detail
tokens_to_check = ['REMI', 'JC', 'DEXR', 'BONKFILES', 'DROPS']

print("Checking tokens without prices in detail...")
print("=" * 80)

for ticker in tokens_to_check:
    # Get the full record
    response = supabase.table('crypto_calls').select('*').eq('ticker', ticker).limit(1).execute()
    
    if response.data:
        token = response.data[0]
        print(f"\n{ticker} ({token['network']})")
        print(f"Contract: {token['contract_address']}")
        print(f"Created: {token['created_at']}")
        
        # Check what data we have
        print(f"Has contract?: {'Yes' if token['contract_address'] else 'No'}")
        print(f"Has raw_data?: {'Yes' if token['raw_data'] else 'No'}")
        
        # Check if contract is in raw_data
        if token['raw_data'] and 'token' in token['raw_data']:
            raw_contract = token['raw_data'].get('token', {}).get('ca')
            print(f"Contract in raw_data: {raw_contract}")
            if raw_contract and not token['contract_address']:
                print("⚠️  Contract exists in raw_data but not in contract_address field!")
        
        # Check price-related fields
        print(f"price_at_call: {token['price_at_call']}")
        print(f"current_price: {token['current_price']}")
        print(f"price_updated_at: {token['price_updated_at']}")
        print(f"price_fetched_at: {token['price_fetched_at']}")
        print(f"roi_percent: {token['roi_percent']}")
        print(f"ath_roi_percent: {token['ath_roi_percent']}")
        
        # Check analysis status
        print(f"Call analyzed?: {'Yes' if token['analysis_score'] else 'No'}")
        print(f"X analyzed?: {'Yes' if token['x_analysis_score'] else 'No'}")

# Now let's check if these are recent calls
print("\n\n" + "=" * 80)
print("Checking distribution of tokens without prices by date...")

# Get count by month
response = supabase.rpc('execute_sql', {
    'query': """
    SELECT 
        DATE_TRUNC('month', created_at) as month,
        COUNT(*) as count
    FROM crypto_calls
    WHERE price_at_call IS NULL 
    AND current_price IS NULL
    GROUP BY month
    ORDER BY month DESC
    """
}).execute()

print("\nTokens without prices by month:")
for row in response.data:
    print(f"{row['month']}: {row['count']} tokens")

# Check if these tokens have contracts
response = supabase.rpc('execute_sql', {
    'query': """
    SELECT 
        CASE 
            WHEN contract_address IS NOT NULL THEN 'Has contract'
            WHEN raw_data->'token'->>'ca' IS NOT NULL THEN 'Contract in raw_data only'
            ELSE 'No contract'
        END as contract_status,
        COUNT(*) as count
    FROM crypto_calls
    WHERE price_at_call IS NULL 
    AND current_price IS NULL
    GROUP BY contract_status
    """
}).execute()

print("\n\nContract status for tokens without prices:")
for row in response.data:
    print(f"{row['contract_status']}: {row['count']} tokens")

# Check a specific example - BONKFILES on Solana
print("\n\n" + "=" * 80)
print("Deep dive on BONKFILES (Solana)...")
response = supabase.table('crypto_calls').select('*').eq('ticker', 'BONKFILES').eq('network', 'solana').limit(1).execute()

if response.data:
    token = response.data[0]
    print(f"Contract address field: {token['contract_address']}")
    if token['raw_data'] and 'token' in token['raw_data']:
        print(f"Contract in raw_data: {token['raw_data']['token'].get('ca')}")
    print(f"Created: {token['created_at']}")
    print(f"Network: {token['network']}")
    
    # This token should be fetchable - it's on Solana with a contract
    if token['contract_address']:
        print(f"\n✅ This token SHOULD be able to get prices!")
        print(f"DexScreener URL: https://dexscreener.com/solana/{token['contract_address']}")