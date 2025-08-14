#!/usr/bin/env python3
"""
Fetch ALL tokens from Supabase and run CA verification on them
"""

import os
import sys
sys.path.append('/Users/marcschwyn/Desktop/projects/KROMV12')

from dotenv import load_dotenv
from supabase import create_client
from verify_all_tokens import IntelligentCAVerifier
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
print("FETCHING ALL TOKENS FROM SUPABASE")
print("="*80)

supabase = create_client(supabase_url, supabase_key)

# Fetch all tokens with websites
response = supabase.table('crypto_calls').select(
    'ticker',
    'network', 
    'contract_address',
    'website_url'
).not_.is_('website_url', 'null').execute()

tokens = response.data

print(f"✅ Found {len(tokens)} tokens with websites in Supabase")

# Remove duplicates based on ticker+network+contract
unique_tokens = {}
for token in tokens:
    key = f"{token['ticker']}_{token['network']}_{token['contract_address']}"
    if key not in unique_tokens:
        unique_tokens[key] = token

print(f"✅ {len(unique_tokens)} unique tokens after deduplication")

# Save to local database
conn = sqlite3.connect('all_tokens_ca_verification.db')
cursor = conn.cursor()

# Create tables
cursor.execute("""
    CREATE TABLE IF NOT EXISTS tokens (
        ticker TEXT,
        network TEXT,
        contract_address TEXT,
        website_url TEXT,
        PRIMARY KEY (ticker, network, contract_address)
    )
""")

cursor.execute("""
    CREATE TABLE IF NOT EXISTS ca_verification_results (
        ticker TEXT,
        network TEXT,
        contract_address TEXT,
        website_url TEXT,
        verdict TEXT,
        found_location TEXT,
        location_type TEXT,
        urls_checked INTEGER,
        error TEXT,
        verified_at TIMESTAMP,
        PRIMARY KEY (ticker, network, contract_address)
    )
""")

# Insert tokens
for token in unique_tokens.values():
    cursor.execute("""
        INSERT OR REPLACE INTO tokens (ticker, network, contract_address, website_url)
        VALUES (?, ?, ?, ?)
    """, (token['ticker'], token['network'], token['contract_address'], token['website_url']))

conn.commit()
print(f"✅ Saved {len(unique_tokens)} tokens to local database")

# Run CA verification
print("\n" + "="*80)
print("STARTING CA VERIFICATION")
print("="*80)

verifier = IntelligentCAVerifier(headless=True)

total = len(unique_tokens)
legitimate = 0
fake = 0
errors = 0
no_website = 0

for i, (key, token) in enumerate(unique_tokens.items(), 1):
    print(f"\n[{i}/{total}] {token['ticker']} on {token['network']}")
    print(f"  Website: {token['website_url'] if token['website_url'] else 'None'}")
    
    if not token['website_url']:
        no_website += 1
        verdict = 'NO_WEBSITE'
        print(f"  ⚫ No website")
    else:
        result = verifier.analyze_and_verify(
            token['website_url'],
            token['contract_address'],
            token['ticker']
        )
        
        if result.get('error'):
            errors += 1
            verdict = 'ERROR'
            print(f"  ❌ Error: {result['error'][:50]}")
        elif result['found']:
            legitimate += 1
            verdict = 'LEGITIMATE'
            print(f"  ✅ LEGITIMATE - Found at: {result['location'][:50] if result['location'] else 'unknown'}")
        else:
            fake += 1
            verdict = 'FAKE'
            print(f"  🚫 FAKE - Not found after checking {len(result.get('checked_urls', []))} pages")
    
    # Save result
    cursor.execute("""
        INSERT OR REPLACE INTO ca_verification_results
        (ticker, network, contract_address, website_url, verdict, 
         found_location, location_type, urls_checked, error, verified_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        token['ticker'],
        token['network'],
        token['contract_address'],
        token['website_url'],
        verdict,
        result.get('location') if verdict == 'LEGITIMATE' else None,
        result.get('location_type') if verdict == 'LEGITIMATE' else None,
        len(result.get('checked_urls', [])) if verdict != 'NO_WEBSITE' else 0,
        result.get('error') if verdict == 'ERROR' else None,
        datetime.now().isoformat()
    ))
    conn.commit()
    
    # Progress update
    if i % 10 == 0:
        print(f"\n--- Progress: {i}/{total} ({i/total*100:.1f}%) ---")
        print(f"✅ Legitimate: {legitimate}, 🚫 Fake: {fake}, ❌ Errors: {errors}")

# Final summary
print("\n" + "="*80)
print("VERIFICATION COMPLETE")
print("="*80)
print(f"Total tokens: {total}")
print(f"✅ Legitimate: {legitimate} ({legitimate/total*100:.1f}%)")
print(f"🚫 Fake: {fake} ({fake/total*100:.1f}%)")
print(f"⚫ No website: {no_website} ({no_website/total*100:.1f}%)")
print(f"❌ Errors: {errors} ({errors/total*100:.1f}%)")

conn.close()

print(f"\n✅ Results saved to: all_tokens_ca_verification.db")
print("View with: sqlite3 all_tokens_ca_verification.db 'SELECT * FROM ca_verification_results'")