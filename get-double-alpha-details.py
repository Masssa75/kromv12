#!/usr/bin/env python3
"""Get details for double ALPHA calls"""

import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(url, key)

print("Fetching double ALPHA calls details...")
print("=" * 60)

# The 3 tickers that got ALPHA from both
double_alpha_tickers = ['THIS YOU?', 'BINANCIENS', 'CASE']

for ticker in double_alpha_tickers:
    print(f"\nTicker: {ticker}")
    print("-" * 40)
    
    # Get all instances of this ticker with double ALPHA
    result = supabase.table('crypto_calls') \
        .select('*') \
        .eq('ticker', ticker) \
        .eq('analysis_tier', 'ALPHA') \
        .eq('x_analysis_tier', 'ALPHA') \
        .execute()
    
    for call in result.data:
        print(f"Created: {call.get('created_at')}")
        print(f"Contract Address: {call.get('contract_address', 'N/A')}")
        print(f"Network: {call.get('network', 'N/A')}")
        
        # Check if raw_data has the contract address
        raw_data = call.get('raw_data')
        if raw_data:
            if isinstance(raw_data, str):
                try:
                    raw_data = json.loads(raw_data)
                except:
                    pass
            
            if isinstance(raw_data, dict):
                # Try different possible fields
                ca = raw_data.get('contract_address') or \
                     raw_data.get('contractAddress') or \
                     raw_data.get('token_address') or \
                     raw_data.get('tokenAddress') or \
                     raw_data.get('address')
                
                if ca:
                    print(f"Contract (from raw_data): {ca}")
                
                # Also print the message
                message = raw_data.get('text', '')[:200]
                print(f"Message: {message}...")
        
        print(f"Claude Description: {call.get('analysis_description', 'N/A')[:100]}...")
        print(f"X Summary: {call.get('x_analysis_summary', 'N/A')[:100]}...")
        print()