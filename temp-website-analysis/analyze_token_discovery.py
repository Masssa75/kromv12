#!/usr/bin/env python3
"""
Analyze websites from token_discovery table
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
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Need service role for writes
supabase: Client = create_client(supabase_url, supabase_key)

def fetch_tokens_with_websites():
    """Fetch all tokens from token_discovery that have websites"""
    try:
        # Query tokens that have websites
        response = supabase.table('token_discovery').select(
            'contract_address, symbol, name, network, website_url, twitter_url, telegram_url, discord_url, first_seen_at, initial_liquidity_usd, initial_volume_24h'
        ).not_.is_('website_url', 'null').order('initial_liquidity_usd', desc=True).execute()
        
        tokens = response.data
        print(f"Found {len(tokens)} tokens with websites from token_discovery table")
        
        # Show top 10 by liquidity
        print("\nTop 10 tokens by liquidity:")
        for i, token in enumerate(tokens[:10], 1):
            liquidity = token.get('initial_liquidity_usd', 0) or 0
            print(f"{i}. {token['symbol']:10} - ${liquidity:,.0f} liquidity - {token['website_url']}")
        
        return tokens
    except Exception as e:
        print(f"Error fetching tokens: {e}")
        return []

def analyze_tokens(tokens):
    """Run website analysis on tokens"""
    # Initialize analyzer with a new database for token_discovery results
    analyzer = ComprehensiveWebsiteAnalyzer('token_discovery_analysis.db')
    
    print(f"\nStarting analysis of {len(tokens)} tokens...")
    print("=" * 80)
    
    analyzed_count = 0
    failed_count = 0
    skipped_count = 0
    
    for i, token in enumerate(tokens, 1):
        symbol = token['symbol']
        website_url = token['website_url']
        
        print(f"\n[{i}/{len(tokens)}] Analyzing {symbol}...")
        print(f"  Website: {website_url}")
        print(f"  Liquidity: ${token.get('initial_liquidity_usd', 0):,.0f}")
        
        # Check if already analyzed
        import sqlite3
        conn = sqlite3.connect('token_discovery_analysis.db')
        cursor = conn.cursor()
        cursor.execute("SELECT total_score FROM website_analysis WHERE ticker = ?", (symbol,))
        existing = cursor.fetchone()
        conn.close()
        
        if existing:
            print(f"  ✓ Already analyzed (Score: {existing[0]}/21)")
            skipped_count += 1
            continue
        
        try:
            # Parse website with a timeout
            print(f"  Parsing website...")
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("Parsing timeout")
            
            # Set a 30 second timeout for parsing
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(30)
            
            try:
                parsed_data = analyzer.parse_website_with_playwright(website_url)
                signal.alarm(0)  # Cancel the alarm
            except TimeoutError:
                print(f"  ✗ Parsing timed out after 30 seconds")
                failed_count += 1
                continue
            
            if not parsed_data or not parsed_data.get('content'):
                print(f"  ✗ Failed to parse website")
                failed_count += 1
                continue
            
            # Analyze with Kimi K2
            print(f"  Running AI analysis...")
            ai_analyses = analyzer.analyze_with_models(parsed_data, models_to_test=[
                ("moonshotai/kimi-k2", "Kimi K2")
            ])
            
            if ai_analyses and len(ai_analyses) > 0:
                analysis = ai_analyses[0]
                
                # Store in database using the save_to_database method
                # Add ticker and metadata to parsed_data for storage
                parsed_data['ticker'] = symbol
                parsed_data['metadata'] = {
                    'source': 'token_discovery',
                    'contract_address': token['contract_address'],
                    'network': token['network'],
                    'initial_liquidity_usd': token.get('initial_liquidity_usd'),
                    'initial_volume_24h': token.get('initial_volume_24h'),
                    'twitter_url': token.get('twitter_url'),
                    'telegram_url': token.get('telegram_url'),
                    'discord_url': token.get('discord_url'),
                    'discovered_at': token.get('first_seen_at')
                }
                
                # Save to database
                analyzer.save_to_database(
                    url=website_url,
                    parsed_data=parsed_data,
                    ai_analyses=[analysis]
                )
                
                score = analysis.get('analysis', {}).get('total_score', 0)
                proceed = analysis.get('analysis', {}).get('proceed_to_stage_2', False)
                print(f"  ✓ Analysis complete - Score: {score}/21 - Stage 2: {proceed}")
                analyzed_count += 1
                
                # Add delay to respect rate limits
                time.sleep(2)
            else:
                print(f"  ✗ AI analysis failed")
                failed_count += 1
                
        except Exception as e:
            print(f"  ✗ Error: {e}")
            failed_count += 1
            continue
    
    print("\n" + "=" * 80)
    print(f"Analysis Complete!")
    print(f"  Analyzed: {analyzed_count}")
    print(f"  Skipped (already done): {skipped_count}")
    print(f"  Failed: {failed_count}")
    print(f"  Total: {len(tokens)}")
    
    return analyzed_count, failed_count, skipped_count

def main():
    print("Token Discovery Website Analysis")
    print("=" * 80)
    
    # Fetch tokens
    tokens = fetch_tokens_with_websites()
    
    if not tokens:
        print("No tokens found with websites")
        return
    
    # Analyze tokens
    analyze_tokens(tokens)
    
    print("\n✓ Analysis complete! Run the viewer to see results:")
    print("  python3 token_discovery_viewer.py")
    print("  Then visit http://localhost:5007")

if __name__ == "__main__":
    main()