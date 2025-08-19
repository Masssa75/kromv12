#!/usr/bin/env python3
"""
Test script for batch website analysis
No user input required - runs automatically
"""
from comprehensive_website_analyzer import ComprehensiveWebsiteAnalyzer
import sqlite3

def test_batch_analysis():
    print("\n" + "="*80)
    print("TESTING BATCH WEBSITE ANALYSIS")
    print("="*80)
    
    analyzer = ComprehensiveWebsiteAnalyzer()
    
    # First, let's see what websites we have to analyze
    conn = sqlite3.connect("website_analysis_new.db")
    cursor = conn.cursor()
    
    # Check how many websites need analysis
    cursor.execute("""
        SELECT COUNT(DISTINCT website_url) 
        FROM tokens 
        WHERE website_url IS NOT NULL 
        AND website_url != ''
    """)
    total_count = cursor.fetchone()[0]
    
    # Check how many are already analyzed
    cursor.execute("""
        SELECT COUNT(DISTINCT url) 
        FROM website_analysis 
        WHERE parse_success = 1
    """)
    analyzed_count = cursor.fetchone()[0]
    
    # Get next 3 websites to analyze
    cursor.execute("""
        SELECT DISTINCT website_url, ticker
        FROM tokens 
        WHERE website_url IS NOT NULL 
        AND website_url != ''
        AND website_url NOT IN (
            SELECT url FROM website_analysis WHERE parse_success = 1
        )
        LIMIT 3
    """)
    
    websites = cursor.fetchall()
    conn.close()
    
    print(f"\n📊 Database Status:")
    print(f"  • Total websites in database: {total_count}")
    print(f"  • Already analyzed: {analyzed_count}")
    print(f"  • Remaining to analyze: {total_count - analyzed_count}")
    
    if not websites:
        print("\n✅ All websites have been analyzed!")
        return
    
    print(f"\n🎯 Will analyze {len(websites)} websites:")
    for url, ticker in websites:
        print(f"  • {ticker}: {url}")
    
    print("\n" + "-"*60)
    
    # Analyze each website
    for i, (url, ticker) in enumerate(websites, 1):
        print(f"\n[{i}/{len(websites)}] Analyzing {ticker}: {url}")
        print("-"*60)
        
        try:
            result = analyzer.analyze_single_website(url)
            
            if result and result['ai_analyses']:
                # Show summary
                scores = [a['analysis'].get('score', 0) for a in result['ai_analyses']]
                avg_score = sum(scores) / len(scores) if scores else 0
                
                team_counts = [len(a['analysis'].get('team_members', [])) for a in result['ai_analyses']]
                avg_team = sum(team_counts) / len(team_counts) if team_counts else 0
                
                print(f"\n📈 Results for {ticker}:")
                print(f"  • Average Score: {avg_score:.1f}/10")
                print(f"  • Avg Team Members Found: {avg_team:.1f}")
                print(f"  • Documents Found: {len(result['parsed_data'].get('documents', []))}")
                print(f"  • LinkedIn Profiles: {len(result['parsed_data'].get('team_data', {}).get('linkedin_profiles', []))}")
                
        except Exception as e:
            print(f"  ❌ Error analyzing {ticker}: {e}")
    
    print("\n" + "="*80)
    print("✅ BATCH ANALYSIS COMPLETE")
    print("="*80)
    print("\n📁 Results saved to website_analysis_new.db")
    print("🌐 View results at http://localhost:5004")

if __name__ == "__main__":
    test_batch_analysis()