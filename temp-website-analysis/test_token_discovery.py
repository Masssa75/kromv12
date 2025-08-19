#!/usr/bin/env python3
"""
Test analyzing a few token discovery websites
"""

import os
import sys
import json
import time
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
from comprehensive_website_analyzer import ComprehensiveWebsiteAnalyzer

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

def test_analysis():
    """Test with just a few tokens"""
    
    # Fetch just 5 tokens with websites
    response = supabase.table('token_discovery').select(
        'contract_address, symbol, name, network, website_url, initial_liquidity_usd'
    ).not_.is_('website_url', 'null').order('initial_liquidity_usd', desc=True).limit(5).execute()
    
    tokens = response.data
    print(f"Testing with {len(tokens)} tokens:")
    for token in tokens:
        print(f"  - {token['symbol']}: {token['website_url']} (${token.get('initial_liquidity_usd', 0):,.0f})")
    
    # Initialize analyzer
    print("\nInitializing analyzer...")
    analyzer = ComprehensiveWebsiteAnalyzer('token_discovery_analysis.db')
    
    # Analyze first token
    if tokens:
        token = tokens[0]
        symbol = token['symbol']
        website_url = token['website_url']
        
        print(f"\nAnalyzing {symbol}...")
        print(f"  Website: {website_url}")
        
        try:
            # Parse website
            print("  Parsing website...")
            parsed_data = analyzer.parse_website_with_playwright(website_url)
            
            if not parsed_data or not parsed_data.get('content'):
                print("  ✗ Failed to parse website")
                return
            
            print(f"  ✓ Parsed {len(parsed_data.get('content', ''))} characters")
            
            # Analyze with Kimi K2
            print("  Running AI analysis...")
            ai_analyses = analyzer.analyze_with_models(parsed_data, models_to_test=[
                ("moonshotai/kimi-k2", "Kimi K2")
            ])
            
            if ai_analyses and len(ai_analyses) > 0:
                analysis = ai_analyses[0]
                score = analysis.get('analysis', {}).get('total_score', 0)
                proceed = analysis.get('analysis', {}).get('proceed_to_stage_2', False)
                print(f"  ✓ Analysis complete - Score: {score}/21 - Stage 2: {proceed}")
                
                # Save to database
                print("  Saving to database...")
                # First add the ticker to parsed_data for storage
                parsed_data['ticker'] = symbol
                parsed_data['metadata'] = {
                    'source': 'token_discovery',
                    'contract_address': token['contract_address'],
                    'network': token['network'],
                    'initial_liquidity_usd': token.get('initial_liquidity_usd')
                }
                analyzer.save_to_database(
                    url=website_url,
                    parsed_data=parsed_data,
                    ai_analyses=[analysis]
                )
                print("  ✓ Saved successfully")
            else:
                print("  ✗ AI analysis failed")
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_analysis()