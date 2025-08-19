#!/usr/bin/env python3
"""Analyze newly added tokens with websites that haven't been analyzed yet"""

import os
import sqlite3
from dotenv import load_dotenv
from supabase import create_client
from comprehensive_website_analyzer import ComprehensiveWebsiteAnalyzer
import json
import time

load_dotenv()

# Connect to Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(supabase_url, supabase_key)

# Get already analyzed tokens
conn = sqlite3.connect('token_discovery_analysis.db')
cursor = conn.cursor()
cursor.execute("SELECT DISTINCT ticker FROM website_analysis")
analyzed_tickers = {row[0] for row in cursor.fetchall()}
conn.close()

print(f"Already analyzed: {len(analyzed_tickers)} tokens")

# Get all tokens with websites from token_discovery
response = supabase.table('token_discovery').select(
    'symbol, contract_address, network, website_url, initial_liquidity_usd, initial_volume_24h, first_seen_at'
).not_.is_('website_url', 'null').order('initial_liquidity_usd', desc=True).execute()

new_tokens = [t for t in response.data if t['symbol'] not in analyzed_tickers]
print(f"New tokens to analyze: {len(new_tokens)}")

if new_tokens:
    print("\nNew tokens found:")
    for token in new_tokens[:10]:  # Show first 10
        print(f"  - {token['symbol']:10} ${token.get('initial_liquidity_usd', 0):,.0f} - {token['website_url']}")
    
    # Initialize analyzer
    analyzer = ComprehensiveWebsiteAnalyzer('token_discovery_analysis.db')
    
    print(f"\nStarting analysis of {len(new_tokens)} new tokens...")
    
    for i, token in enumerate(new_tokens, 1):
        symbol = token['symbol']
        website_url = token['website_url']
        
        print(f"\n[{i}/{len(new_tokens)}] Analyzing {symbol}")
        print(f"  URL: {website_url}")
        
        try:
            # Parse website
            parsed_data = analyzer.parse_website_with_playwright(website_url)
            
            if not parsed_data or not parsed_data.get('content'):
                print("  ✗ Failed to parse")
                parsed_data = {'success': False, 'content': '', 'navigation': {'all_links': []}}
            
            # Add metadata
            parsed_data['ticker'] = symbol
            parsed_data['metadata'] = {
                'source': 'token_discovery',
                'contract_address': token['contract_address'],
                'network': token['network'],
                'initial_liquidity_usd': token.get('initial_liquidity_usd'),
                'initial_volume_24h': token.get('initial_volume_24h'),
                'discovered_at': token.get('first_seen_at')
            }
            
            # Analyze with AI
            ai_analyses = analyzer.analyze_with_models(parsed_data, models_to_test=[
                ("moonshotai/kimi-k2", "Kimi K2")
            ])
            
            if ai_analyses and len(ai_analyses) > 0:
                analysis = ai_analyses[0]
                score = analysis.get('analysis', {}).get('total_score', 0)
                print(f"  ✓ Score: {score}/21")
            else:
                analysis = {
                    'model': 'Kimi K2',
                    'analysis': {
                        'total_score': 0,
                        'proceed_to_stage_2': False,
                        'category_scores': {},
                        'exceptional_signals': [],
                        'missing_elements': ['Analysis failed']
                    }
                }
                ai_analyses = [analysis]
                print(f"  ✗ Analysis failed")
            
            # Save to database
            analyzer.save_to_database(
                url=website_url,
                parsed_data=parsed_data,
                ai_analyses=ai_analyses
            )
            
            time.sleep(2)  # Rate limit
            
        except Exception as e:
            print(f"  ✗ Error: {str(e)[:100]}")
            continue
    
    print(f"\n✓ Analyzed {len(new_tokens)} new tokens")
else:
    print("\nNo new tokens to analyze!")