#!/usr/bin/env python3
"""Test updated system with all navigation links"""

from comprehensive_website_analyzer import ComprehensiveWebsiteAnalyzer
import json

def test_token(ticker, url):
    """Test a single token with the updated system"""
    analyzer = ComprehensiveWebsiteAnalyzer()
    
    print(f"\n{'='*60}")
    print(f"Testing {ticker}: {url}")
    print('='*60)
    
    # Parse website
    parsed_data = analyzer.parse_website_with_playwright(url)
    parsed_data['ticker'] = ticker
    
    if parsed_data.get('success'):
        # Show navigation links found
        all_links = parsed_data.get('navigation', {}).get('all_links', [])
        print(f"✅ Parsing successful")
        print(f"📍 Found {len(all_links)} navigation links")
        
        # Show link breakdown
        high_priority = [l for l in all_links if l.get('priority') == 'high']
        medium_priority = [l for l in all_links if l.get('priority') == 'medium']
        print(f"   - High priority: {len(high_priority)}")
        print(f"   - Medium priority: {len(medium_priority)}")
        print(f"   - Other: {len(all_links) - len(high_priority) - len(medium_priority)}")
        
        print("\n🔗 High Priority Links:")
        for link in high_priority[:5]:
            print(f"   [{link.get('type')}] {link.get('text')}: {link.get('url')}")
        
        # Analyze with AI
        print(f"\n🤖 Analyzing with AI (Kimi K2 only for speed)...")
        ai_analyses = analyzer.analyze_with_models(parsed_data, models_to_test=[
            ("kimi/kimi-k2", "Kimi K2")
        ])
        
        if ai_analyses:
            analysis = ai_analyses[0]['analysis']
            print(f"\n📊 Results:")
            print(f"Total Score: {analysis.get('total_score')}/21")
            print(f"Proceed to Stage 2: {analysis.get('proceed_to_stage_2')}")
            
            # Show Stage 2 links selected
            stage_2_links = analysis.get('stage_2_links', [])
            print(f"\n✅ AI Selected {len(stage_2_links)} Links for Stage 2:")
            for i, link in enumerate(stage_2_links, 1):
                # Check if this link was in the navigation
                was_in_nav = any(nav_link['url'] == link for nav_link in all_links)
                status = "✓ from navigation" if was_in_nav else "⚠️ not in navigation list"
                print(f"   {i}. {link} ({status})")
            
            # Save to database
            analyzer.save_to_database(url, parsed_data, ai_analyses)
            print(f"\n💾 Saved to database")
            
            return True
    else:
        print(f"❌ Parsing failed: {parsed_data.get('error')}")
        return False

def main():
    # Test a few tokens
    test_cases = [
        ('LIQUID', 'https://liquidagent.ai'),
        ('PAYAI', 'https://payai.org'),
    ]
    
    for ticker, url in test_cases:
        test_token(ticker, url)
    
    print("\n" + "="*60)
    print("✅ Testing complete! Check http://localhost:5006 to see the updated UI")
    print("="*60)

if __name__ == "__main__":
    main()