#!/usr/bin/env python3
"""
Test the verification on just a few tokens first
"""

from verify_all_tokens import IntelligentCAVerifier
import sqlite3

# Get first 3 tokens
conn = sqlite3.connect('analysis_results.db')
cursor = conn.cursor()

cursor.execute("""
    SELECT DISTINCT ticker, network, contract_address, website_url
    FROM website_analysis
    WHERE website_url IS NOT NULL
    ORDER BY website_score DESC
    LIMIT 3
""")

tokens = cursor.fetchall()
conn.close()

print("="*60)
print("TESTING CA VERIFIER ON 3 TOKENS")
print("="*60)

verifier = IntelligentCAVerifier(headless=True)

for ticker, network, contract, website in tokens:
    print(f"\nTesting: {ticker}")
    print(f"Website: {website}")
    print(f"Contract: {contract[:30]}...")
    
    result = verifier.analyze_and_verify(website, contract, ticker)
    
    if result.get('error'):
        print(f"❌ Error: {result['error']}")
    elif result['found']:
        print(f"✅ FOUND at: {result['location']}")
        print(f"   Type: {result['location_type']}")
    else:
        print(f"🚫 NOT FOUND")
        print(f"   Checked {len(result.get('checked_urls', []))} pages")

print("\nTest complete!")