#!/usr/bin/env python3
"""Test KAI and LENS tokens with automatic Stage 2 qualifiers"""

from comprehensive_website_analyzer import ComprehensiveWebsiteAnalyzer
import json

def test_tokens():
    # Test tokens with docs and apps
    test_cases = [
        {
            'ticker': 'KAI',
            'url': 'https://kaikostudios.xyz',
            'expected': 'Should qualify for Stage 2 if it has docs'
        },
        {
            'ticker': 'LENS', 
            'url': 'https://getlensnow.com/',
            'expected': 'Should qualify for Stage 2 - has installable apps'
        }
    ]
    
    analyzer = ComprehensiveWebsiteAnalyzer()
    
    for test in test_cases:
        print(f"\n{'='*60}")
        print(f"Testing {test['ticker']}: {test['url']}")
        print(f"Expected: {test['expected']}")
        print('='*60)
        
        # Parse website
        parsed_data = analyzer.parse_website_with_playwright(test['url'])
        parsed_data['ticker'] = test['ticker']
        
        if parsed_data.get('success'):
            print(f"✅ Parsing successful")
            print(f"📄 Documents found: {len(parsed_data.get('documents', []))}")
            
            # Show document types
            for doc in parsed_data.get('documents', [])[:5]:
                print(f"   - {doc.get('type')}: {doc.get('text')} - {doc.get('url')[:60]}...")
            
            # Analyze with AI
            print(f"\n🤖 Analyzing with AI...")
            ai_analyses = analyzer.analyze_with_models(parsed_data)
            
            if ai_analyses:
                analysis = ai_analyses[0]['analysis']
                print(f"\n📊 Results:")
                print(f"Total Score: {analysis.get('total_score')}/21")
                print(f"Tier: {analysis.get('tier')}")
                print(f"Proceed to Stage 2: {analysis.get('proceed_to_stage_2')}")
                
                # Show automatic qualifiers
                auto_qualifiers = analysis.get('automatic_stage_2_qualifiers', [])
                if auto_qualifiers:
                    print(f"\n🎯 Automatic Stage 2 Qualifiers Found:")
                    for qualifier in auto_qualifiers:
                        print(f"   ✓ {qualifier}")
                else:
                    print(f"\n❌ No automatic qualifiers found")
                
                # Show Stage 2 links
                stage_2_links = analysis.get('stage_2_links', [])
                if stage_2_links:
                    print(f"\n🔗 Recommended for Stage 2 analysis:")
                    for link in stage_2_links[:5]:
                        print(f"   - {link}")
                
                # Category breakdown
                print(f"\n📈 Category Scores:")
                categories = analysis.get('category_scores', {})
                for cat, score in categories.items():
                    print(f"   {cat}: {score}/3")
                
                print(f"\n💡 Assessment: {analysis.get('quick_assessment')}")
            
            # Save to database
            analyzer.save_to_database(test['url'], parsed_data, ai_analyses)
            print(f"\n💾 Saved to database")
        else:
            print(f"❌ Parsing failed: {parsed_data.get('error')}")

if __name__ == "__main__":
    test_tokens()