#!/usr/bin/env python3
"""Simple batch runner for testing"""
from comprehensive_website_analyzer import ComprehensiveWebsiteAnalyzer
import sqlite3
import time

# URLs to test
test_urls = [
    ('STRAT', 'https://www.ethstrat.xyz/'),
    ('REX', 'https://www.etherex.finance/'),
    ('MAMO', 'https://mamo.bot/'),
    ('PAWSE', 'https://pawse.xyz/'),
    ('GRAY', 'https://www.gradient.trade/')
]

print("Starting simple batch test...")
analyzer = ComprehensiveWebsiteAnalyzer()
models = [("moonshotai/kimi-k2", "Kimi K2")]

for ticker, url in test_urls:
    print(f"\n{ticker}: {url}")
    
    try:
        # Parse
        parsed = analyzer.parse_website_with_playwright(url)
        
        if parsed['success']:
            # Analyze
            results = analyzer.analyze_with_models(parsed, models_to_test=models)
            print(f"  ✅ Success")
            
            # Check it was saved
            conn = sqlite3.connect('website_analysis_new.db')
            cursor = conn.cursor()
            cursor.execute("SELECT score FROM website_analysis WHERE url = ? ORDER BY analyzed_at DESC LIMIT 1", (url,))
            result = cursor.fetchone()
            if result:
                print(f"  📊 Score: {result[0]}/10")
            conn.close()
        else:
            print(f"  ❌ Parse failed")
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:100]}")
    
    time.sleep(2)

# Final check
conn = sqlite3.connect('website_analysis_new.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(DISTINCT url) FROM website_analysis")
count = cursor.fetchone()[0]
conn.close()

print(f"\n✅ Total unique URLs in database: {count}")