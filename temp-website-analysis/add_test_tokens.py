#!/usr/bin/env python3
"""Add test tokens with proper tickers"""

from comprehensive_website_analyzer import ComprehensiveWebsiteAnalyzer
import time

analyzer = ComprehensiveWebsiteAnalyzer(db_path='website_analysis_new.db')

test_tokens = [
    ("GAI", "https://www.graphai.tech/"),
    ("MSIA", "https://messiah.network"),
    ("STRAT", "https://www.ethstrat.xyz/"),
]

print("Adding test tokens with proper tickers...")

for ticker, url in test_tokens:
    print(f"\n[{ticker}] Analyzing {url}...")
    
    try:
        parsed_data = analyzer.parse_website_with_playwright(url)
        parsed_data['ticker'] = ticker
        
        if parsed_data['success']:
            results = analyzer.analyze_with_models(
                parsed_data, 
                models_to_test=[("moonshotai/kimi-k2", "Kimi K2")]
            )
            
            if results:
                analysis = results[0]['analysis']
                total = analysis.get('total_score', 0)
                tier = analysis.get('tier', 'LOW')
                print(f"  ✅ {ticker}: {total}/21 ({tier})")
        else:
            print(f"  ❌ Parse failed")
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:100]}")
    
    time.sleep(1)

print("\n✅ Test tokens added! Check http://localhost:5005")