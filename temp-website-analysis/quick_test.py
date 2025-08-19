#!/usr/bin/env python3
"""Quick test of improved prompt"""

from comprehensive_website_analyzer import ComprehensiveWebsiteAnalyzer

analyzer = ComprehensiveWebsiteAnalyzer(db_path='website_analysis_new.db')

# Test MSIA
url = "https://www.graphai.tech/"
print(f"\n{'='*60}\nTesting: {url}\n{'='*60}")

parsed_data = analyzer.parse_website_with_playwright(url)
parsed_data['ticker'] = 'GAI'  # Set the ticker manually
if parsed_data['success']:
    print(f"Parsed: {len(parsed_data['content']['text'])} chars")
    
    # Just test with Kimi K2
    results = analyzer.analyze_with_models(parsed_data, models_to_test=[("moonshotai/kimi-k2", "Kimi K2")])
    result = results[0] if results else None
    if result:
        analysis = result['analysis']
        print(f"\n✨ Total Score: {analysis.get('total_score')}/21")
        print(f"📊 Tier: {analysis.get('tier')}")
        print(f"🎯 Proceed to Stage 2: {'YES ✅' if analysis.get('proceed_to_stage_2') else 'NO ❌'}")
        
        # Display category scores
        category_scores = analysis.get('category_scores', {})
        if category_scores:
            print(f"\n📊 Category Scores (1-3 scale):")
            print(f"  Technical Infrastructure: {category_scores.get('technical_infrastructure', 0)}/3")
            print(f"  Business & Utility:       {category_scores.get('business_utility', 0)}/3")
            print(f"  Documentation Quality:    {category_scores.get('documentation_quality', 0)}/3")
            print(f"  Community & Social:       {category_scores.get('community_social', 0)}/3")
            print(f"  Security & Trust:         {category_scores.get('security_trust', 0)}/3")
            print(f"  Team Transparency:        {category_scores.get('team_transparency', 0)}/3")
            print(f"  Website Presentation:     {category_scores.get('website_presentation', 0)}/3")
        
        exceptional = analysis.get('exceptional_signals', [])
        if exceptional:
            print(f"\n✨ Exceptional Signals:")
            for signal in exceptional:
                print(f"  • {signal}")
        
        missing = analysis.get('missing_elements', [])
        if missing:
            print(f"\n⚠️ Missing Elements:")
            for element in missing:
                print(f"  • {element}")
        
        print(f"\n📝 Quick Assessment: {analysis.get('quick_assessment')}")
        
        # Save it
        analyzer.save_to_database(url, parsed_data, [result])
        print("\n✅ Saved to database")
    else:
        print("Analysis failed")
else:
    print(f"Parse failed: {parsed_data.get('error')}")