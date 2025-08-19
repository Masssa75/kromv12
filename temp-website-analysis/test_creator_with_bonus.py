#!/usr/bin/env python3
"""
Test CREATOR with improved prompt that looks for extraordinary achievements
"""
from comprehensive_website_analyzer import ComprehensiveWebsiteAnalyzer
import json

def test_creator():
    analyzer = ComprehensiveWebsiteAnalyzer()
    url = "https://creatordao.com"
    
    print("Testing CREATOR with improved prompt")
    print("="*60)
    
    # Parse the website
    parsed_data = analyzer.parse_website_with_playwright(url)
    parsed_data['ticker'] = "CREATOR"
    
    if not parsed_data['success']:
        print("Parse failed")
        return
    
    # The content includes Kong with 4M subscribers and $50M revenue
    content = parsed_data['content'].get('text', '')
    print(f"✅ Content captured: {len(content)} chars")
    
    # Verify extraordinary achievements are in the content
    if "4 million" in content:
        print("✅ Found: 4 million subscribers")
    if "$50" in content or "50+ million" in content:
        print("✅ Found: $50+ million in revenue")
    if "YC-backed" in content:
        print("✅ Found: YC-backed founder")
        
    # Now analyze with AI using improved prompt
    print("\n🤖 Analyzing with improved prompt...")
    models = [("moonshotai/kimi-k2", "Kimi K2")]
    results = analyzer.analyze_with_models(parsed_data, models_to_test=models)
    
    if results and len(results) > 0:
        analysis = results[0]['analysis']
        score = analysis.get('total_score', 0)
        exceptional = analysis.get('exceptional_signals', [])
        
        print(f"\n📊 Results:")
        print(f"   Score: {score}/21")
        print(f"   Tier: {analysis.get('tier', 'UNKNOWN')}")
        
        if exceptional:
            print(f"\n🌟 Exceptional signals found:")
            for signal in exceptional:
                print(f"   - {signal}")
        else:
            print(f"\n❌ No exceptional signals detected")
            
        # Show category scores
        print(f"\n📈 Category scores:")
        categories = analysis.get('category_scores', {})
        for cat, score in categories.items():
            print(f"   {cat}: {score}/3")
            
        # Save to file for inspection
        with open('creator_improved_analysis.json', 'w') as f:
            json.dump(analysis, f, indent=2)
        print(f"\n💾 Full analysis saved to creator_improved_analysis.json")

if __name__ == "__main__":
    test_creator()