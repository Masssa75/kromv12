#!/usr/bin/env python3
"""Test analyzing a single token"""

print("Starting test...", flush=True)

from comprehensive_website_analyzer import ComprehensiveWebsiteAnalyzer
import sqlite3

print("Initializing...", flush=True)
analyzer = ComprehensiveWebsiteAnalyzer()
models = [("moonshotai/kimi-k2", "Kimi K2")]

# Test one token
url = "https://www.ethstrat.xyz/"
ticker = "STRAT"

print(f"\nAnalyzing {ticker}: {url}", flush=True)

try:
    parsed = analyzer.parse_website_with_playwright(url)
    if parsed['success']:
        results = analyzer.analyze_with_models(parsed, models_to_test=models)
        print("✅ Success!", flush=True)
        
        # Check result
        conn = sqlite3.connect('website_analysis_new.db')
        cursor = conn.cursor()
        cursor.execute("""
            SELECT score, team_members_found 
            FROM website_analysis 
            WHERE url = ? 
            ORDER BY analyzed_at DESC 
            LIMIT 1
        """, (url,))
        result = cursor.fetchone()
        if result:
            print(f"Score: {result[0]}/10, Team: {result[1]}", flush=True)
        conn.close()
    else:
        print(f"❌ Parse failed: {parsed.get('error')}", flush=True)
except Exception as e:
    print(f"❌ Error: {e}", flush=True)

print("Done!", flush=True)