#!/usr/bin/env python3
"""Test PHI and VIRUS websites with loading screen detection"""

import os
import sys
from comprehensive_website_analyzer import ComprehensiveWebsiteAnalyzer

# Test websites with loading screens
test_sites = [
    ('PHI', 'https://www.phiprotocol.ai'),
    ('VIRUS', 'https://virusonsol.com/')  # Assuming this is the URL
]

# Get VIRUS URL from database first
import sqlite3
conn = sqlite3.connect('/Users/marcschwyn/Desktop/projects/KROMV12/temp-website-analysis/website_analysis_new.db')
cursor = conn.cursor()
cursor.execute("SELECT ticker, url FROM website_analysis WHERE ticker = 'VIRUS'")
virus_result = cursor.fetchone()
if virus_result:
    test_sites[1] = (virus_result[0], virus_result[1])
conn.close()

print("🧪 Testing websites with loading screens")
print("=" * 60)

# Initialize analyzer
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, 'website_analysis_new.db')
analyzer = ComprehensiveWebsiteAnalyzer(db_path=db_path)

for ticker, url in test_sites:
    print(f"\n📊 Testing {ticker}: {url}")
    print("-" * 50)
    
    # Parse website
    parsed_data = analyzer.parse_website_with_playwright(url)
    parsed_data['ticker'] = ticker
    
    if parsed_data.get('success'):
        content_length = len(parsed_data.get('content', {}).get('text', ''))
        print(f"  ✅ Parsing succeeded")
        print(f"  📝 Content length: {content_length} chars")
        
        # Show first 200 chars of content
        content_preview = parsed_data.get('content', {}).get('text', '')[:200]
        print(f"  📄 Content preview: {content_preview}")
        
        # Try AI analysis
        print("\n  🤖 Testing AI analysis...")
        ai_analyses = analyzer.analyze_with_models(parsed_data, models_to_test=[
            ("moonshotai/kimi-k2", "Kimi K2")
        ])
        
        if ai_analyses and ai_analyses[0].get('analysis'):
            score = ai_analyses[0]['analysis'].get('total_score', 0)
            print(f"  ✅ AI analysis succeeded! Score: {score}/21")
            
            # Show some details
            analysis = ai_analyses[0]['analysis']
            print(f"  🏢 Business utility score: {analysis.get('category_scores', {}).get('business_utility', 0)}/3")
            print(f"  📚 Documentation score: {analysis.get('category_scores', {}).get('documentation_quality', 0)}/3")
            print(f"  👥 Team transparency score: {analysis.get('category_scores', {}).get('team_transparency', 0)}/3")
        else:
            print("  ❌ AI analysis failed")
    else:
        print(f"  ❌ Parsing failed: {parsed_data.get('error')}")

print("\n" + "=" * 60)
print("✅ Test complete!")