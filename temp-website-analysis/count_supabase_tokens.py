#!/usr/bin/env python3
"""
Quick check of how many tokens are in Supabase
"""

import os
import sys
sys.path.append('/Users/marcschwyn/Desktop/projects/KROMV12')

from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv('/Users/marcschwyn/Desktop/projects/KROMV12/.env')

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not supabase_url or not supabase_key:
    print("❌ Supabase credentials not found")
    exit(1)

supabase = create_client(supabase_url, supabase_key)

# Count all tokens
print("Checking Supabase for tokens with websites...")

response = supabase.table('crypto_calls').select(
    'ticker',
    'network', 
    'contract_address',
    'website_url'
).not_.is_('website_url', 'null').execute()

tokens = response.data
print(f"✅ Total tokens with websites: {len(tokens)}")

# Count unique
unique_tokens = {}
for token in tokens:
    key = f"{token['ticker']}_{token['network']}_{token['contract_address']}"
    if key not in unique_tokens:
        unique_tokens[key] = token

print(f"✅ Unique tokens: {len(unique_tokens)}")

# Show sample
print("\nSample tokens:")
for i, (key, token) in enumerate(list(unique_tokens.items())[:5], 1):
    print(f"{i}. {token['ticker']} on {token['network']}: {token['website_url']}")