#!/usr/bin/env python3
"""
Analyze next batch of utility tokens (6-10) with high AI scores
"""

import os
import sys
sys.path.append('..')
from dotenv import load_dotenv
import requests
import time

# Load environment variables
load_dotenv('../.env')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

def get_next_utility_tokens():
    headers = {
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
        'Content-Type': 'application/json'
    }
    
    print("=" * 80)
    print("ANALYZING UTILITY TOKENS 6-10 WITH HIGH AI SCORES")
    print("=" * 80)
    
    # Query for utility tokens with websites, ordered by best AI score
    query = '''
        select=id,ticker,network,website_url,analysis_score,x_analysis_score,ath_roi_percent,contract_address
        &website_url=not.is.null
        &analysis_token_type=eq.utility
        &is_dead=is.false
        &order=analysis_score.desc.nullsfirst,x_analysis_score.desc.nullsfirst
        &limit=30
    '''.replace('\n', '').replace('    ', '')
    
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls?{query}"
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        tokens = response.json()
        
        # Sort by max of analysis_score and x_analysis_score
        tokens_sorted = sorted(tokens, 
                              key=lambda x: max(x.get('analysis_score') or 0, 
                                              x.get('x_analysis_score') or 0), 
                              reverse=True)
        
        # Skip first 5 (already analyzed) and take next 5
        selected_tokens = tokens_sorted[5:10]
        
        print(f"\nAnalyzing tokens 6-10:")
        print("-" * 80)
        print(f"{'#':<3} {'Ticker':<10} {'Network':<10} {'AI':<4} {'X-AI':<5} {'Website':<40}")
        print("-" * 80)
        
        for i, t in enumerate(selected_tokens, 6):
            ai_score = t.get('analysis_score') or 0
            x_score = t.get('x_analysis_score') or 0
            website = t['website_url'][:40] + "..." if len(t['website_url']) > 40 else t['website_url']
            print(f"→ {i:<2} {t['ticker']:<10} {t['network']:<10} {ai_score:<4} {x_score:<5} {website}")
        
        return selected_tokens
    else:
        print(f"Error fetching from Supabase: {response.status_code}")
        return []

if __name__ == "__main__":
    # Get tokens 6-10
    tokens = get_next_utility_tokens()
    
    if tokens:
        print("\n" + "=" * 80)
        print("Starting website analysis with summaries...")
        print("=" * 80)
        
        # Import and run the analyzer
        from website_analyzer import WebsiteAnalyzer
        
        analyzer = WebsiteAnalyzer()
        
        for i, token in enumerate(tokens, 1):
            print(f"\n[{i}/5] Processing {token['ticker']}...")
            
            # Analyze website
            analysis = analyzer.analyze_website(token)
            
            # Save results
            analyzer.save_analysis(token, analysis)
            
            if analysis:
                score = analysis.get('website_score', 0)
                tier = analysis.get('website_tier', 'UNKNOWN')
                print(f"  ✓ Analysis complete: Score {score}/10, Tier: {tier}")
                if analysis.get('website_summary'):
                    print(f"  Summary preview: {analysis['website_summary'][:100]}...")
            else:
                print(f"  ✗ Analysis failed")
            
            # Rate limiting
            if i < len(tokens):
                time.sleep(3)
        
        print("\n" + "=" * 80)
        print("Analysis Complete!")
        stats = analyzer.get_stats()
        print(f"Total analyzed: {stats['total']}")
        print(f"Average score: {stats['avg_score']}/10")
        print("=" * 80)
        print("\nView results at: http://localhost:5000")
        print("Or open viewer-standalone.html directly")