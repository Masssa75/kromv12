#!/usr/bin/env python3
"""
Database Backup Script
Creates a JSON backup of critical market cap related fields
"""

import os
import json
import warnings
warnings.filterwarnings("ignore")
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Initialize Supabase
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_file = f"database_backup_{timestamp}.json"

print("=" * 60)
print(f"Creating Database Backup: {backup_file}")
print("=" * 60)

# Fetch all tokens with relevant market cap fields
print("\nFetching all crypto_calls data...")
result = supabase.table('crypto_calls').select(
    'id,krom_id,ticker,contract_address,pool_address,network,'
    'price_at_call,current_price,ath_price,'
    'market_cap_at_call,current_market_cap,ath_market_cap,'
    'total_supply,circulating_supply,supply_updated_at,'
    'volume_24h,liquidity_usd,is_dead'
).limit(5000).execute()

tokens = result.data
print(f"Retrieved {len(tokens)} tokens")

# Save to JSON file
print(f"\nSaving backup to {backup_file}...")
with open(backup_file, 'w') as f:
    json.dump({
        'timestamp': timestamp,
        'total_records': len(tokens),
        'data': tokens
    }, f, indent=2, default=str)

# Get file size
file_size = os.path.getsize(backup_file)
print(f"✅ Backup created successfully!")
print(f"   File: {backup_file}")
print(f"   Size: {file_size / 1024 / 1024:.2f} MB")
print(f"   Records: {len(tokens)}")

# Show sample of backed up data
print("\nSample of backed up tokens:")
for token in tokens[:5]:
    print(f"  {token['ticker']}: MC@Call={token.get('market_cap_at_call')}, "
          f"Supply={token.get('total_supply')}")

print("\n" + "=" * 60)
print("Backup complete! You can now safely proceed with updates.")
print("=" * 60)