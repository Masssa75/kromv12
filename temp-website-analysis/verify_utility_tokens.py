#!/usr/bin/env python3
"""
Verify CA for the utility tokens we fetched
"""

from verify_all_tokens import IntelligentCAVerifier
import sqlite3
from datetime import datetime

# Get tokens from database
conn = sqlite3.connect('utility_tokens_ca.db')
cursor = conn.cursor()

cursor.execute("SELECT ticker, network, contract_address, website_url FROM tokens ORDER BY liquidity_usd DESC")
tokens = cursor.fetchall()

print("="*80)
print(f"CA VERIFICATION - {len(tokens)} UTILITY TOKENS")
print("="*80)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*80)

# Create results table
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
conn.commit()

# Initialize verifier
verifier = IntelligentCAVerifier(headless=True)

# Track stats
stats = {
    'legitimate': 0,
    'fake': 0,
    'error': 0,
    'total': len(tokens)
}

# Process each token
for i, (ticker, network, contract, website) in enumerate(tokens, 1):
    print(f"\n[{i}/{len(tokens)}] {ticker} on {network}")
    print(f"  Website: {website[:60]}...")
    
    # Verify
    result = verifier.analyze_and_verify(website, contract, ticker)
    
    # Determine verdict
    if result.get('error'):
        verdict = 'ERROR'
        stats['error'] += 1
        print(f"  ❌ ERROR: {result['error'][:50]}")
    elif result['found']:
        verdict = 'LEGITIMATE'
        stats['legitimate'] += 1
        print(f"  ✅ LEGITIMATE - Found at: {result.get('location', 'unknown')[:50]}")
    else:
        verdict = 'FAKE'
        stats['fake'] += 1
        print(f"  🚫 FAKE - Not found after checking {len(result.get('checked_urls', []))} pages")
    
    # Save result
    cursor.execute("""
        INSERT OR REPLACE INTO ca_verification_results
        (ticker, network, contract_address, website_url, verdict,
         found_location, location_type, urls_checked, error, verified_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        ticker, network, contract, website, verdict,
        result.get('location'), result.get('location_type'),
        len(result.get('checked_urls', [])),
        result.get('error'), datetime.now().isoformat()
    ))
    conn.commit()
    
    # Progress update
    if i % 10 == 0:
        print(f"\n--- Progress: {i}/{len(tokens)} ({i/len(tokens)*100:.1f}%) ---")
        print(f"✅ Legitimate: {stats['legitimate']}, 🚫 Fake: {stats['fake']}, ❌ Errors: {stats['error']}")

# Final summary
print("\n" + "="*80)
print("VERIFICATION COMPLETE")
print("="*80)
print(f"Total tokens: {stats['total']}")
print(f"✅ Legitimate: {stats['legitimate']} ({stats['legitimate']/stats['total']*100:.1f}%)")
print(f"🚫 Fake: {stats['fake']} ({stats['fake']/stats['total']*100:.1f}%)")
print(f"❌ Errors: {stats['error']} ({stats['error']/stats['total']*100:.1f}%)")
print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

conn.close()

print(f"\n✅ Results saved to utility_tokens_ca.db")
print("Table: ca_verification_results")