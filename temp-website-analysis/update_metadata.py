#!/usr/bin/env python3
"""Update metadata in website_analysis with contract addresses from token_discovery"""

import os
import sqlite3
import json
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# Connect to Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(supabase_url, supabase_key)

# Get all tokens from token_discovery
response = supabase.table('token_discovery').select(
    'symbol, contract_address, network, website_url, initial_liquidity_usd, initial_volume_24h, first_seen_at'
).not_.is_('website_url', 'null').execute()

token_data = {t['symbol']: t for t in response.data}
print(f"Loaded {len(token_data)} tokens from token_discovery")

# Update website_analysis database
conn = sqlite3.connect('token_discovery_analysis.db')
cursor = conn.cursor()

# Get all analyzed tokens
cursor.execute("SELECT id, ticker FROM website_analysis")
analyzed = cursor.fetchall()

updated = 0
for id_, ticker in analyzed:
    if ticker in token_data:
        token = token_data[ticker]
        metadata = {
            'source': 'token_discovery',
            'contract_address': token['contract_address'],
            'network': token['network'],
            'initial_liquidity_usd': token.get('initial_liquidity_usd'),
            'initial_volume_24h': token.get('initial_volume_24h'),
            'discovered_at': token.get('first_seen_at')
        }
        
        cursor.execute(
            "UPDATE website_analysis SET metadata = ? WHERE id = ?",
            (json.dumps(metadata), id_)
        )
        updated += 1

conn.commit()
print(f"Updated {updated} records with metadata")

# Verify
cursor.execute("SELECT COUNT(*) FROM website_analysis WHERE metadata IS NOT NULL")
count = cursor.fetchone()[0]
print(f"Total records with metadata: {count}")

# Show sample
cursor.execute("SELECT ticker, metadata FROM website_analysis WHERE metadata IS NOT NULL LIMIT 3")
for ticker, metadata in cursor.fetchall():
    meta = json.loads(metadata)
    print(f"\n{ticker}:")
    print(f"  Contract: {meta.get('contract_address')}")
    print(f"  Network: {meta.get('network')}")

conn.close()