#!/usr/bin/env python3
"""
Simple batch analyzer for utility tokens - Kimi K2 only
"""
import sys
import sqlite3
import time

print("Starting batch analyzer...", flush=True)
sys.stdout.flush()

from comprehensive_website_analyzer import ComprehensiveWebsiteAnalyzer
print("Imported analyzer", flush=True)

# Initialize
analyzer = ComprehensiveWebsiteAnalyzer()
models = [("moonshotai/kimi-k2", "Kimi K2")]

# Get tokens
tokens_conn = sqlite3.connect('utility_tokens_ca.db')
cursor = tokens_conn.cursor()
cursor.execute("""
    SELECT DISTINCT ticker, website_url, liquidity_usd 
    FROM tokens 
    WHERE website_url IS NOT NULL
    ORDER BY liquidity_usd DESC NULLS LAST
""")
all_tokens = cursor.fetchall()

# Get already analyzed
analysis_conn = sqlite3.connect('website_analysis_new.db')
analysis_cursor = analysis_conn.cursor()
analysis_cursor.execute("SELECT DISTINCT url FROM website_analysis")
analyzed = set(row[0] for row in analysis_cursor.fetchall())

# Normalize for comparison
def normalize_url(url):
    """Remove www variations for comparison"""
    return url.replace('https://www.', 'https://').replace('http://www.', 'http://')

analyzed_normalized = set(normalize_url(u) for u in analyzed)

# Filter tokens
to_analyze = []
for ticker, url, liquidity in all_tokens:
    if normalize_url(url) not in analyzed_normalized:
        to_analyze.append((ticker, url, liquidity))

print(f"\n{'='*70}")
print(f"BATCH ANALYSIS - KIMI K2")
print(f"{'='*70}")
print(f"Total: {len(all_tokens)} | Analyzed: {len(analyzed)} | To do: {len(to_analyze)}")
print(f"{'='*70}\n")

if not to_analyze:
    print("✅ All tokens analyzed!")
    exit()

# Process tokens
success = 0
failed = 0
start_time = time.time()

for i, (ticker, url, liquidity) in enumerate(to_analyze, 1):
    print(f"\n[{i}/{len(to_analyze)}] {ticker}: {url}")
    
    try:
        # Parse
        parsed = analyzer.parse_website_with_playwright(url)
        
        if parsed['success']:
            # Analyze
            results = analyzer.analyze_with_models(parsed, models_to_test=models)
            success += 1
            
            # Get result
            analysis_cursor.execute("""
                SELECT score, team_members_found 
                FROM website_analysis 
                WHERE url = ? 
                ORDER BY analyzed_at DESC 
                LIMIT 1
            """, (url,))
            
            result = analysis_cursor.fetchone()
            if result:
                score, team = result
                print(f"  ✅ Score: {score}/10, Team: {team}")
        else:
            failed += 1
            print(f"  ❌ Parse failed")
            
    except Exception as e:
        failed += 1
        print(f"  ❌ Error: {str(e)[:100]}")
    
    # Progress every 5
    if i % 5 == 0:
        elapsed = (time.time() - start_time) / 60
        rate = i / (elapsed * 60)
        print(f"\n📊 Progress: {i}/{len(to_analyze)} | Rate: {rate*60:.1f}/min | Time: {elapsed:.1f}min")
    
    # Small delay
    time.sleep(1)
    
    # Stop after 10 for testing
    if i >= 10:
        print("\n⚠️  Stopping after 10 for testing. Remove this limit to process all.")
        break

# Summary
print(f"\n{'='*70}")
print(f"SUMMARY: ✅ {success} | ❌ {failed} | Time: {(time.time()-start_time)/60:.1f}min")
print(f"{'='*70}")

tokens_conn.close()
analysis_conn.close()