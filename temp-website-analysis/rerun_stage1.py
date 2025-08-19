#!/usr/bin/env python3
"""Rerun existing tokens with new 1-3 scoring"""

from comprehensive_website_analyzer import ComprehensiveWebsiteAnalyzer
import time

analyzer = ComprehensiveWebsiteAnalyzer(db_path='website_analysis_new.db')

# Test tokens
test_urls = [
    ("MSIA", "https://messiah.network"),
    ("STRAT", "https://www.ethstrat.xyz/"),
    ("REX", "https://www.etherex.finance/"),
    ("GAI", "https://www.graphai.tech/"),
    ("TRWA", "https://tharwa.finance/"),
    ("BLOCK", "https://www.blockstreet.xyz/"),
]

print("="*60)
print("RERUNNING TOKENS WITH STAGE 1 ASSESSMENT (1-3 SCALE)")
print("="*60)

for ticker, url in test_urls:
    print(f"\n[{ticker}] Analyzing {url}...")
    
    try:
        # Parse website
        parsed_data = analyzer.parse_website_with_playwright(url)
        parsed_data['ticker'] = ticker
        
        if parsed_data['success']:
            # Analyze with Kimi K2
            results = analyzer.analyze_with_models(
                parsed_data, 
                models_to_test=[("moonshotai/kimi-k2", "Kimi K2")]
            )
            
            if results:
                analysis = results[0]['analysis']
                total = analysis.get('total_score', 0)
                tier = analysis.get('tier', 'LOW')
                proceed = analysis.get('proceed_to_stage_2', False)
                
                print(f"  ✅ Score: {total}/21 ({tier})")
                print(f"  {'🟢 PROCEED to Stage 2' if proceed else '🔴 SKIP Stage 2'}")
                
                # Show exceptional signals if any
                exceptional = analysis.get('exceptional_signals', [])
                if exceptional:
                    print(f"  ✨ Exceptional: {', '.join(exceptional[:2])}")
        else:
            print(f"  ❌ Parse failed")
            
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:100]}")
    
    # Small delay
    time.sleep(2)

print("\n" + "="*60)
print("✅ Rerun complete! Check http://localhost:5005 for results")
print("="*60)