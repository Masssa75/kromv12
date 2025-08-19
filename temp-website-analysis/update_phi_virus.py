#!/usr/bin/env python3
"""Manually update PHI and VIRUS with full re-analysis"""

import os
import sys
import sqlite3
import json
from datetime import datetime
from comprehensive_website_analyzer import ComprehensiveWebsiteAnalyzer

# Sites to update
sites_to_update = [
    ('PHI', 'https://www.phiprotocol.ai'),
    ('VIRUS', 'https://www.pndm.org/')
]

# Initialize analyzer
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, 'website_analysis_new.db')
analyzer = ComprehensiveWebsiteAnalyzer(db_path=db_path)

print("🔄 Re-analyzing and updating PHI and VIRUS with full results")
print("=" * 60)

for ticker, url in sites_to_update:
    print(f"\n📊 Processing {ticker}: {url}")
    print("-" * 50)
    
    # Parse website with full extraction
    parsed_data = analyzer.parse_website_with_playwright(url)
    parsed_data['ticker'] = ticker
    
    if parsed_data.get('success'):
        content_length = len(parsed_data.get('content', {}).get('text', ''))
        print(f"  ✅ Parsing succeeded - {content_length} chars extracted")
        
        # Show what links were found
        all_links = parsed_data.get('navigation', {}).get('all_links', [])
        high_priority_links = [l for l in all_links if l.get('priority') == 'high']
        print(f"  🔗 Found {len(all_links)} total links ({len(high_priority_links)} high priority)")
        
        if high_priority_links:
            print("  📎 High priority links:")
            for link in high_priority_links[:3]:
                print(f"    - {link.get('text', 'N/A')}: {link.get('url', '')[:60]}...")
        
        # Analyze with AI
        print("  🤖 Running AI analysis...")
        ai_analyses = analyzer.analyze_with_models(parsed_data, models_to_test=[
            ("moonshotai/kimi-k2", "Kimi K2")
        ])
        
        if ai_analyses and ai_analyses[0].get('analysis'):
            analysis = ai_analyses[0]['analysis']
            score = analysis.get('total_score', 0)
            print(f"  ✅ AI analysis complete! Score: {score}/21")
            
            # Show category breakdown
            categories = analysis.get('category_scores', {})
            print("  📊 Category scores:")
            for cat, val in categories.items():
                print(f"    - {cat}: {val}/3")
            
            # Show if AI recommended Stage 2
            stage2_recommended = analysis.get('proceed_to_stage_2', False)
            auto_qualifiers = analysis.get('automatic_stage_2_qualifiers', [])
            print(f"  🎯 Stage 2 recommended: {stage2_recommended}")
            if auto_qualifiers:
                print(f"  🚀 Auto-qualifiers: {', '.join(auto_qualifiers)}")
            
            # Extract data for database update
            team_members = analysis.get('team_members', [])
            
            # Now update the database with FULL results
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Delete existing record if any
            cursor.execute("DELETE FROM website_analysis WHERE ticker = ? AND url = ?", (ticker, url))
            
            # Insert new complete record
            cursor.execute("""
                INSERT INTO website_analysis 
                (ticker, url, parsed_content, documents_found, team_members_found, 
                 linkedin_profiles, score, tier, legitimacy_indicators, 
                 red_flags, technical_depth, team_transparency, business_utility,
                 community_strength, security_measures, reasoning, 
                 analyzed_at, parse_success, parse_error,
                 score_technical_infrastructure, score_business_utility,
                 score_documentation_quality, score_community_social,
                 score_security_trust, score_team_transparency,
                 score_website_presentation, category_scores,
                 total_score, proceed_to_stage_2, exceptional_signals,
                 missing_elements, quick_assessment, stage_2_links, 
                 automatic_stage_2_qualifiers)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ticker,
                url,
                json.dumps(parsed_data),  # This includes all navigation links in parsed_content
                len(parsed_data.get('documents', [])),
                len(team_members),
                len(parsed_data.get('team_data', {}).get('linkedin_profiles', [])),
                score,  # Old score column
                analysis.get('tier', 'LOW'),
                json.dumps(analysis.get('legitimacy_indicators', [])),
                json.dumps(analysis.get('red_flags', [])),
                analysis.get('technical_depth', ''),
                analysis.get('team_transparency', ''),
                analysis.get('business_utility', ''),
                analysis.get('community_strength', ''),
                analysis.get('security_measures', ''),
                analysis.get('reasoning', ''),
                datetime.now().isoformat(),
                parsed_data.get('success', False),
                parsed_data.get('error', ''),
                categories.get('technical_infrastructure', 0),
                categories.get('business_utility', 0),
                categories.get('documentation_quality', 0),
                categories.get('community_social', 0),
                categories.get('security_trust', 0),
                categories.get('team_transparency', 0),
                categories.get('website_presentation', 0),
                json.dumps(categories),
                score,  # total_score column
                stage2_recommended,
                json.dumps(analysis.get('exceptional_signals', [])),
                json.dumps(analysis.get('missing_elements', [])),
                analysis.get('quick_assessment', ''),
                json.dumps(analysis.get('stage_2_links', [])),
                json.dumps(auto_qualifiers)
            ))
            
            conn.commit()
            conn.close()
            
            print(f"  💾 Database updated successfully!")
            
        else:
            print("  ❌ AI analysis failed")
    else:
        print(f"  ❌ Parsing failed: {parsed_data.get('error')}")

print("\n" + "=" * 60)
print("✅ Update complete! PHI and VIRUS have been fully re-analyzed and saved.")