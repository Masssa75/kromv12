#!/usr/bin/env python3
"""
Run batch analysis on utility tokens - simple approach
"""
from comprehensive_website_analyzer import ComprehensiveWebsiteAnalyzer
import sqlite3
import time

# Get tokens to analyze
tokens_conn = sqlite3.connect('utility_tokens_ca.db')
cursor = tokens_conn.cursor()
cursor.execute("""
    SELECT DISTINCT ticker, website_url 
    FROM tokens 
    WHERE website_url IS NOT NULL
    ORDER BY liquidity_usd DESC NULLS LAST
    LIMIT 20
""")
tokens = cursor.fetchall()
tokens_conn.close()

# Check what's analyzed
analysis_conn = sqlite3.connect('website_analysis_new.db')
analysis_cursor = analysis_conn.cursor()
analysis_cursor.execute("SELECT DISTINCT url FROM website_analysis")
analyzed = set(row[0].replace('https://www.', 'https://').replace('http://www.', 'http://') 
               for row in analysis_cursor.fetchall())
analysis_conn.close()

# Filter
to_analyze = []
for ticker, url in tokens:
    normalized = url.replace('https://www.', 'https://').replace('http://www.', 'http://')
    if normalized not in analyzed:
        to_analyze.append((ticker, url))

print(f"\nAnalyzing {len(to_analyze)} tokens (first 20 unanalyzed)")
print("="*60)

# Initialize
analyzer = ComprehensiveWebsiteAnalyzer()
models = [("moonshotai/kimi-k2", "Kimi K2")]

# Process
for i, (ticker, url) in enumerate(to_analyze, 1):
    print(f"\n[{i}/{len(to_analyze)}] {ticker}: {url}")
    
    try:
        parsed = analyzer.parse_website_with_playwright(url)
        if parsed['success']:
            results = analyzer.analyze_with_models(parsed, models_to_test=models)
            print(f"  ✅ Success")
        else:
            print(f"  ❌ Parse failed")
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:100]}")
    
    time.sleep(1)

print("\n✅ Batch complete!")