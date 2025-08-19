#!/usr/bin/env python3
"""Test improved prompt on specific tokens"""

import sys
from comprehensive_website_analyzer import ComprehensiveWebsiteAnalyzer

def test_single_website(url):
    """Test the improved prompt on a single website"""
    analyzer = ComprehensiveWebsiteAnalyzer(db_path='website_analysis_new.db')
    
    print(f"\n{'='*60}")
    print(f"Testing improved prompt on: {url}")
    print(f"{'='*60}\n")
    
    # Parse website
    parsed_data = analyzer.parse_website_with_playwright(url)
    if not parsed_data['success']:
        print(f"❌ Failed to parse: {parsed_data.get('error')}")
        return
    
    print(f"✅ Parsed {len(parsed_data['content']['text'])} chars")
    print(f"📄 Documents: {len(parsed_data.get('documents', []))}")
    print(f"👥 LinkedIn profiles: {len(parsed_data.get('team_data', {}).get('linkedin_profiles', []))}")
    
    # Analyze with Kimi K2 (cheapest and most accurate)
    ai_analyses = []
    result = analyzer.analyze_with_ai(parsed_data, model='kimi-k2')
    if result:
        ai_analyses.append(result)
        score = result['analysis'].get('score', 0)
        team_count = len(result['analysis'].get('team_members', []))
        print(f"\n🤖 Kimi K2 Analysis:")
        print(f"  Score: {score}/10")
        print(f"  Team members: {team_count}")
        print(f"  Business utility: {result['analysis'].get('business_utility', 'N/A')}")
        print(f"  Community strength: {result['analysis'].get('community_strength', 'N/A')}")
        print(f"  Security measures: {result['analysis'].get('security_measures', 'N/A')}")
        print(f"  Technical depth: {result['analysis'].get('technical_depth', 'N/A')}")
        print(f"  Team transparency: {result['analysis'].get('team_transparency', 'N/A')}")
        print(f"\n  Reasoning: {result['analysis'].get('reasoning', 'N/A')}")
        
        # Save to database
        analyzer.save_to_database(url, parsed_data, ai_analyses)
        print(f"\n💾 Saved to database")
    else:
        print("❌ Analysis failed")

if __name__ == "__main__":
    # Test these specific tokens
    test_urls = [
        "https://messiah.network",  # MSIA - should score higher now
        "https://www.ethstrat.xyz/",  # STRAT - should score higher now
        "https://www.etherex.finance/"  # REX - should score higher now
    ]
    
    if len(sys.argv) > 1:
        # Allow testing specific URL from command line
        test_urls = [sys.argv[1]]
    
    for url in test_urls:
        test_single_website(url)
    
    print(f"\n{'='*60}")
    print("✅ Testing complete!")
    print("Check the database or run the UI to see the new scores")
    print(f"{'='*60}")