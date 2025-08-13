#!/usr/bin/env python3
"""
Analyze top utility tokens with high AI scores
"""

import os
import sys
sys.path.append('..')
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv('../.env')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

def get_top_utility_tokens(limit=30):
    headers = {
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
        'Content-Type': 'application/json'
    }
    
    print("=" * 80)
    print("TOP UTILITY TOKENS WITH HIGH AI SCORES AND WEBSITES")
    print("=" * 80)
    
    # Query for utility tokens with websites, ordered by best AI score (either call or X analysis)
    query = '''
        select=id,ticker,network,website_url,analysis_score,x_analysis_score,ath_roi_percent,contract_address
        &website_url=not.is.null
        &analysis_token_type=eq.utility
        &is_dead=is.false
        &order=analysis_score.desc.nullsfirst,x_analysis_score.desc.nullsfirst
        &limit={}
    '''.format(limit).replace('\n', '').replace('    ', '')
    
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls?{query}"
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        tokens = response.json()
        
        # Sort by max of analysis_score and x_analysis_score
        tokens_sorted = sorted(tokens, 
                              key=lambda x: max(x.get('analysis_score') or 0, 
                                              x.get('x_analysis_score') or 0), 
                              reverse=True)
        
        print(f"\nFound {len(tokens_sorted)} utility tokens with websites")
        print("-" * 80)
        print(f"{'#':<3} {'Ticker':<10} {'Network':<10} {'AI':<4} {'X-AI':<5} {'ROI%':<10} {'Website':<40}")
        print("-" * 80)
        
        for i, t in enumerate(tokens_sorted[:30], 1):
            ai_score = t.get('analysis_score') or 0
            x_score = t.get('x_analysis_score') or 0
            max_score = max(ai_score, x_score)
            roi = f"{t['ath_roi_percent']:,.0f}%" if t.get('ath_roi_percent') else "N/A"
            website = t['website_url'][:40] + "..." if len(t['website_url']) > 40 else t['website_url']
            
            # Highlight top 5
            if i <= 5:
                print(f"→ {i:<2} {t['ticker']:<10} {t['network']:<10} {ai_score:<4} {x_score:<5} {roi:<10} {website}")
            else:
                print(f"  {i:<2} {t['ticker']:<10} {t['network']:<10} {ai_score:<4} {x_score:<5} {roi:<10} {website}")
        
        print("\n" + "=" * 80)
        print("ANALYZING TOP 5 UTILITY TOKENS...")
        print("=" * 80)
        
        return tokens_sorted[:5]
    else:
        print(f"Error fetching from Supabase: {response.status_code}")
        return []

if __name__ == "__main__":
    # Get top 5 utility tokens
    top_tokens = get_top_utility_tokens(30)
    
    if top_tokens:
        print("\nNow running website_analyzer.py with these 5 tokens...")
        print("-" * 80)
        
        # Import and run the analyzer
        from website_analyzer import WebsiteAnalyzer
        
        analyzer = WebsiteAnalyzer()
        
        for i, token in enumerate(top_tokens, 1):
            print(f"\n[{i}/5] Processing {token['ticker']}...")
            
            # Analyze website
            analysis = analyzer.analyze_website(token)
            
            # Save results
            analyzer.save_analysis(token, analysis)
            
            if analysis:
                score = analysis.get('website_score', 0)
                tier = analysis.get('website_tier', 'UNKNOWN')
                print(f"  ✓ Analysis complete: Score {score}/10, Tier: {tier}")
            else:
                print(f"  ✗ Analysis failed")
        
        print("\n" + "=" * 80)
        print("Analysis Complete!")
        stats = analyzer.get_stats()
        print(f"Total analyzed: {stats['total']}")
        print(f"Average score: {stats['avg_score']}/10")
        print("=" * 80)