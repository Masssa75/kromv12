#!/usr/bin/env python3
"""Quickly add test tokens"""

from comprehensive_website_analyzer import ComprehensiveWebsiteAnalyzer

analyzer = ComprehensiveWebsiteAnalyzer(db_path='website_analysis_new.db')

# Quick test tokens
tokens = [
    ("MSIA", "https://messiah.network"),
    ("STRAT", "https://www.ethstrat.xyz/"),
    ("REX", "https://www.etherex.finance/")
]

for ticker, url in tokens:
    print(f"Adding {ticker}...")
    try:
        parsed_data = analyzer.parse_website_with_playwright(url)
        parsed_data['ticker'] = ticker
        
        if parsed_data['success']:
            results = analyzer.analyze_with_models(
                parsed_data, 
                models_to_test=[("moonshotai/kimi-k2", "Kimi K2")]
            )
            if results:
                print(f"✅ {ticker} added")
        else:
            print(f"❌ {ticker} parse failed")
    except Exception as e:
        print(f"❌ {ticker} error: {e}")

print("Done! Check http://localhost:5006")