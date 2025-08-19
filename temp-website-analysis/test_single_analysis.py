#!/usr/bin/env python3
"""
Test analyzing a single site to debug the None score issue
"""
from comprehensive_website_analyzer import ComprehensiveWebsiteAnalyzer
import json

def test_single_site():
    analyzer = ComprehensiveWebsiteAnalyzer()
    
    # Test with NKP which we know works
    url = "https://nonkyotoprotocol.com/"
    ticker = "NKP"
    
    print(f"Testing analysis for {ticker}: {url}")
    print("="*60)
    
    # Parse the website
    parsed_data = analyzer.parse_website_with_playwright(url)
    parsed_data['ticker'] = ticker
    
    if not parsed_data['success']:
        print(f"❌ Failed to parse: {parsed_data.get('error')}")
        return
    
    print(f"✅ Parsed successfully")
    print(f"   Content length: {len(parsed_data['content'].get('text', ''))} chars")
    
    # Analyze with Kimi K2
    models = [("moonshotai/kimi-k2", "Kimi K2")]
    print("\n🤖 Analyzing with Kimi K2...")
    
    results = analyzer.analyze_with_models(parsed_data, models_to_test=models)
    
    print("\n📊 Analysis Results:")
    print(json.dumps(results, indent=2))
    
    # Check what was saved to database
    import sqlite3
    conn = sqlite3.connect('website_analysis_new.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT ticker, total_score, tier, category_scores, exceptional_signals
        FROM website_analysis 
        WHERE url = ? 
        ORDER BY analyzed_at DESC 
        LIMIT 1
    """, (url,))
    
    row = cursor.fetchone()
    if row:
        print("\n📊 Database entry:")
        print(f"   Ticker: {row[0]}")
        print(f"   Total Score: {row[1]}")
        print(f"   Tier: {row[2]}")
        print(f"   Category Scores: {row[3][:100]}...")
        print(f"   Exceptional Signals: {row[4][:100]}...")
    else:
        print("\n❌ No database entry found")
    
    conn.close()

if __name__ == "__main__":
    test_single_site()