#!/usr/bin/env python3
"""
Fetch non-dead utility tokens from Supabase for CA verification
"""

import os
import sys
sys.path.append('/Users/marcschwyn/Desktop/projects/KROMV12')

from dotenv import load_dotenv
from supabase import create_client
import sqlite3
from datetime import datetime

# Load environment variables
load_dotenv('/Users/marcschwyn/Desktop/projects/KROMV12/.env')

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not supabase_url or not supabase_key:
    print("❌ Supabase credentials not found")
    exit(1)

print("="*80)
print("FETCHING NON-DEAD UTILITY TOKENS FROM SUPABASE")
print("="*80)

supabase = create_client(supabase_url, supabase_key)

# Fetch non-dead tokens with websites
# Non-dead = has liquidity, recent activity, not invalidated
response = supabase.table('crypto_calls').select(
    'ticker',
    'network', 
    'contract_address',
    'website_url',
    'liquidity_usd',
    'current_price',
    'is_invalidated'
).not_.is_('website_url', 'null')\
.is_('is_invalidated', 'false')\
.gt('liquidity_usd', 1000)\
.order('liquidity_usd', desc=True)\
.limit(250)\
.execute()

tokens = response.data

print(f"✅ Found {len(tokens)} non-dead utility tokens with websites")
print(f"   (liquidity > $1000, not invalidated, has website)")

# Save to local database
conn = sqlite3.connect('utility_tokens.db')
cursor = conn.cursor()

# Create table
cursor.execute("""
    CREATE TABLE IF NOT EXISTS utility_tokens (
        ticker TEXT,
        network TEXT,
        contract_address TEXT,
        website_url TEXT,
        liquidity_usd REAL,
        current_price REAL,
        PRIMARY KEY (ticker, network, contract_address)
    )
""")

# Clear existing data
cursor.execute("DELETE FROM utility_tokens")

# Insert tokens
for token in tokens:
    cursor.execute("""
        INSERT INTO utility_tokens (ticker, network, contract_address, website_url, liquidity_usd, current_price)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        token['ticker'],
        token['network'],
        token['contract_address'],
        token['website_url'],
        token['liquidity_usd'],
        token['current_price']
    ))

conn.commit()

# Show summary
cursor.execute("SELECT COUNT(*) FROM utility_tokens")
total = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(DISTINCT network) FROM utility_tokens")
networks = cursor.fetchone()[0]

cursor.execute("SELECT AVG(liquidity_usd) FROM utility_tokens")
avg_liquidity = cursor.fetchone()[0]

print(f"\n📊 Summary:")
print(f"   Total tokens: {total}")
print(f"   Networks: {networks}")
print(f"   Average liquidity: ${avg_liquidity:,.0f}")

# Show top 10
print(f"\n🏆 Top 10 by liquidity:")
cursor.execute("""
    SELECT ticker, network, liquidity_usd, website_url
    FROM utility_tokens
    ORDER BY liquidity_usd DESC
    LIMIT 10
""")

for i, (ticker, network, liquidity, website) in enumerate(cursor.fetchall(), 1):
    print(f"{i:2}. {ticker:10} ({network:10}) ${liquidity:>12,.0f} - {website[:40]}...")

conn.close()

print(f"\n✅ Saved {total} utility tokens to utility_tokens.db")
print("Ready for CA verification!")