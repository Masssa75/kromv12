#!/usr/bin/env python3
"""
Quick batch analyzer for token_discovery websites with better debugging
"""

import os
import sys
import json
import time
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

def get_already_analyzed():
    """Get list of already analyzed tokens"""
    try:
        if not os.path.exists('token_discovery_analysis.db'):
            # Create the database if it doesn't exist
            conn = sqlite3.connect('token_discovery_analysis.db')
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS website_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ticker TEXT,
                    url TEXT,
                    network TEXT,
                    contract_address TEXT,
                    initial_liquidity_usd REAL,
                    parsed_content TEXT,
                    analysis_json TEXT,
                    total_score INTEGER,
                    proceed_to_stage_2 BOOLEAN,
                    category_scores TEXT,
                    exceptional_signals TEXT,
                    missing_elements TEXT,
                    automatic_stage_2_qualifiers TEXT,
                    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            conn.close()
            return set()
        
        conn = sqlite3.connect('token_discovery_analysis.db')
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT ticker FROM website_analysis")
        analyzed = {row[0] for row in cursor.fetchall()}
        conn.close()
        return analyzed
    except Exception as e:
        print(f"Error getting analyzed tokens: {e}")
        return set()

def fetch_tokens_with_websites():
    """Fetch all tokens from token_discovery that have websites"""
    try:
        print("Fetching tokens from Supabase...")
        response = supabase.table('token_discovery').select(
            'contract_address, symbol, name, network, website_url, twitter_url, telegram_url, discord_url, first_seen_at, initial_liquidity_usd, initial_volume_24h'
        ).not_.is_('website_url', 'null').order('initial_liquidity_usd', desc=True).execute()
        
        print(f"Fetched {len(response.data)} tokens with websites")
        return response.data
    except Exception as e:
        print(f"Error fetching tokens: {e}")
        return []

def main():
    """Main function to run analysis"""
    print("=" * 80)
    print("TOKEN DISCOVERY WEBSITE ANALYSIS - QUICK BATCH")
    print("=" * 80)
    
    # Get already analyzed tokens
    already_analyzed = get_already_analyzed()
    print(f"Already analyzed: {len(already_analyzed)} tokens")
    
    # Fetch all tokens
    tokens = fetch_tokens_with_websites()
    print(f"Total tokens with websites: {len(tokens)}")
    
    # Filter out already analyzed
    tokens_to_analyze = [t for t in tokens if t['symbol'] not in already_analyzed]
    print(f"Tokens to analyze: {len(tokens_to_analyze)}")
    
    if not tokens_to_analyze:
        print("\n✅ All tokens already analyzed!")
        return
    
    # Show what we'll analyze
    print("\n📊 Top 10 tokens to analyze (by liquidity):")
    for i, token in enumerate(tokens_to_analyze[:10], 1):
        liquidity = token.get('initial_liquidity_usd', 0) or 0
        print(f"  {i}. {token['symbol']:10} ${liquidity:>10,.0f} - {token['website_url'][:50]}")
    
    print(f"\n🚀 Ready to analyze {len(tokens_to_analyze)} websites")
    print("This will use the comprehensive_website_analyzer.py")
    print("Estimated time: ~15 seconds per website")
    print(f"Total estimated time: {len(tokens_to_analyze) * 15 / 60:.1f} minutes")
    
    # Try importing the analyzer
    try:
        from comprehensive_website_analyzer import ComprehensiveWebsiteAnalyzer
        print("\n✅ Analyzer imported successfully")
    except ImportError as e:
        print(f"\n❌ Error importing analyzer: {e}")
        print("Make sure comprehensive_website_analyzer.py is in the same directory")
        return
    
    # Proceed with all tokens
    print(f"\n✅ Proceeding with all {len(tokens_to_analyze)} tokens")
    
    print("\n" + "=" * 80)
    print(f"Starting Analysis of {len(tokens_to_analyze)} Websites")
    print("=" * 80)
    
    # Initialize analyzer
    analyzer = ComprehensiveWebsiteAnalyzer('token_discovery_analysis.db')
    
    analyzed_count = 0
    failed_count = 0
    start_time = time.time()
    
    for i, token in enumerate(tokens_to_analyze, 1):
        symbol = token['symbol']
        website_url = token['website_url']
        liquidity = token.get('initial_liquidity_usd', 0) or 0
        
        print(f"\n[{i}/{len(tokens_to_analyze)}] Analyzing {symbol}")
        print(f"  URL: {website_url}")
        print(f"  Liquidity: ${liquidity:,.0f}")
        
        try:
            # Parse website
            print(f"  📝 Parsing website...")
            parsed_data = analyzer.parse_website_with_playwright(website_url)
            
            if parsed_data:
                content_length = len(str(parsed_data.get('content', '')))
                print(f"  ✅ Parsed {content_length} characters")
            else:
                print(f"  ⚠️ Failed to parse website")
                continue
            
            # Add metadata
            parsed_data['ticker'] = symbol
            parsed_data['metadata'] = {
                'source': 'token_discovery',
                'contract_address': token['contract_address'],
                'network': token['network'],
                'initial_liquidity_usd': token.get('initial_liquidity_usd'),
                'twitter_url': token.get('twitter_url'),
                'telegram_url': token.get('telegram_url'),
                'discord_url': token.get('discord_url')
            }
            
            # Analyze with AI
            print(f"  🤖 Analyzing with Kimi K2...")
            ai_analyses = analyzer.analyze_with_models(parsed_data, models_to_test=[
                ("moonshotai/kimi-k2", "Kimi K2")
            ])
            
            if ai_analyses:
                analysis = ai_analyses[0]
                score = analysis.get('total_score', 0)
                stage2 = analysis.get('proceed_to_stage_2', False)
                print(f"  📊 Score: {score}/21")
                print(f"  🎯 Stage 2: {'YES' if stage2 else 'NO'}")
                analyzed_count += 1
            else:
                print(f"  ⚠️ No AI analysis returned")
                failed_count += 1
            
            # Wait 2 seconds between requests (API rate limit)
            time.sleep(2)
            
        except Exception as e:
            print(f"  ❌ Error: {str(e)[:100]}")
            failed_count += 1
            continue
    
    elapsed_time = time.time() - start_time
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"✅ Analyzed: {analyzed_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"⏱️ Time elapsed: {elapsed_time/60:.1f} minutes")
    print(f"\nView results at: http://localhost:5007")
    print(f"Run: python3 token_discovery_server.py")

if __name__ == "__main__":
    main()