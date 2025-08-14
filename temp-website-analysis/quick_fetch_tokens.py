#!/usr/bin/env python3
import os, sys
sys.path.append('/Users/marcschwyn/Desktop/projects/KROMV12')
from dotenv import load_dotenv
load_dotenv('/Users/marcschwyn/Desktop/projects/KROMV12/.env')
from supabase import create_client
import sqlite3

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
client = create_client(url, key)

print("Fetching non-dead utility tokens...")

# Get non-dead tokens with websites
response = client.table('crypto_calls').select(
    'ticker, network, contract_address, website_url, liquidity_usd'
).not_.is_('website_url', 'null').is_('is_invalidated', 'false').gt('liquidity_usd', 1000).order('liquidity_usd', desc=True).limit(250).execute()

tokens = response.data
print(f'✅ Found {len(tokens)} non-dead utility tokens')

# Save to database
conn = sqlite3.connect('utility_tokens_ca.db')
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS tokens (
        ticker TEXT,
        network TEXT,
        contract_address TEXT,
        website_url TEXT,
        liquidity_usd REAL,
        PRIMARY KEY (ticker, network, contract_address)
    )
""")

cursor.execute("DELETE FROM tokens")

for token in tokens:
    cursor.execute("""
        INSERT OR REPLACE INTO tokens VALUES (?, ?, ?, ?, ?)
    """, (token['ticker'], token['network'], token['contract_address'], 
          token['website_url'], token['liquidity_usd']))

conn.commit()
conn.close()

print(f'✅ Saved to utility_tokens_ca.db')
print('\nTop 10 by liquidity:')
for i, token in enumerate(tokens[:10], 1):
    liq = int(token['liquidity_usd']) if token['liquidity_usd'] else 0
    print(f"{i:2}. {token['ticker']:8} ({token['network']:8}) ${liq:>10,} - {token['website_url'][:40]}")