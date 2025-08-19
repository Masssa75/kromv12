#!/usr/bin/env python3
"""
Batch analyze all token_discovery websites with better error handling
"""

import os
import sys
import json
import time
import sqlite3
import traceback
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

def get_already_analyzed():
    """Get list of already analyzed tokens"""
    try:
        conn = sqlite3.connect('token_discovery_analysis.db')
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT ticker FROM website_analysis")
        analyzed = {row[0] for row in cursor.fetchall()}
        conn.close()
        return analyzed
    except:
        return set()

def fetch_tokens_with_websites():
    """Fetch all tokens from token_discovery that have websites"""
    try:
        response = supabase.table('token_discovery').select(
            'contract_address, symbol, name, network, website_url, twitter_url, telegram_url, discord_url, first_seen_at, initial_liquidity_usd, initial_volume_24h'
        ).not_.is_('website_url', 'null').order('initial_liquidity_usd', desc=True).execute()
        
        return response.data
    except Exception as e:
        print(f"Error fetching tokens: {e}")
        return []

def safe_parse_website(analyzer, url, max_retries=2):
    """Safely parse website with retries and error handling"""
    for attempt in range(max_retries):
        try:
            # Try parsing
            parsed_data = analyzer.parse_website_with_playwright(url)
            
            # Check if we got valid content
            if parsed_data and parsed_data.get('content'):
                content_length = len(str(parsed_data.get('content', '')))
                if content_length > 10:  # Must have some real content
                    return parsed_data
                else:
                    print(f"    Attempt {attempt+1}: Got minimal content ({content_length} chars)")
            else:
                print(f"    Attempt {attempt+1}: No content extracted")
                
        except Exception as e:
            error_msg = str(e)
            if 'TypeError' in error_msg or 'includes is not a function' in error_msg:
                print(f"    Attempt {attempt+1}: JavaScript error (common issue)")
            else:
                print(f"    Attempt {attempt+1}: {error_msg[:100]}")
        
        if attempt < max_retries - 1:
            time.sleep(2)  # Wait before retry
    
    # If all attempts failed, return minimal parsed data
    return {
        'success': False,
        'content': '',
        'error': 'Failed to parse after retries',
        'navigation': {'all_links': []},
        'documents': [],
        'team_data': {}
    }

def analyze_tokens():
    """Run website analysis on all tokens"""
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
        print("All tokens already analyzed!")
        return
    
    # Initialize analyzer
    analyzer = ComprehensiveWebsiteAnalyzer('token_discovery_analysis.db')
    
    print("\n" + "=" * 80)
    print("Starting Batch Analysis")
    print("=" * 80)
    
    analyzed_count = 0
    failed_count = 0
    start_time = time.time()
    
    for i, token in enumerate(tokens_to_analyze, 1):
        symbol = token['symbol']
        website_url = token['website_url']
        liquidity = token.get('initial_liquidity_usd', 0) or 0
        
        print(f"\n[{i}/{len(tokens_to_analyze)}] {symbol}")
        print(f"  URL: {website_url}")
        print(f"  Liquidity: ${liquidity:,.0f}")
        
        try:
            # Parse website with error handling
            print(f"  Parsing...")
            parsed_data = safe_parse_website(analyzer, website_url)
            
            # Add metadata
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
            
            # Analyze with AI (even if parsing failed, to record the attempt)
            print(f"  Analyzing with AI...")
            try:
                ai_analyses = analyzer.analyze_with_models(parsed_data, models_to_test=[
                    ("moonshotai/kimi-k2", "Kimi K2")
                ])
                
                if ai_analyses and len(ai_analyses) > 0:
                    analysis = ai_analyses[0]
                    score = analysis.get('analysis', {}).get('total_score', 0)
                    proceed = analysis.get('analysis', {}).get('proceed_to_stage_2', False)
                    print(f"  ✓ Score: {score}/21 - Stage 2: {proceed}")
                else:
                    # Create minimal analysis for failed parsing
                    analysis = {
                        'model': 'Kimi K2',
                        'analysis': {
                            'total_score': 0,
                            'proceed_to_stage_2': False,
                            'category_scores': {},
                            'exceptional_signals': [],
                            'missing_elements': ['Failed to parse website'],
                            'reasoning': 'Website could not be parsed'
                        }
                    }
                    ai_analyses = [analysis]
                    print(f"  ✗ Analysis failed - recorded as 0/21")
                    
            except Exception as e:
                print(f"  ✗ AI analysis error: {str(e)[:100]}")
                # Create minimal analysis
                analysis = {
                    'model': 'Kimi K2',
                    'analysis': {
                        'total_score': 0,
                        'proceed_to_stage_2': False,
                        'category_scores': {},
                        'exceptional_signals': [],
                        'missing_elements': ['Analysis error'],
                        'reasoning': f'Error: {str(e)[:200]}'
                    }
                }
                ai_analyses = [analysis]
            
            # Save to database
            try:
                analyzer.save_to_database(
                    url=website_url,
                    parsed_data=parsed_data,
                    ai_analyses=ai_analyses
                )
                analyzed_count += 1
                print(f"  ✓ Saved to database")
            except Exception as e:
                print(f"  ✗ Database error: {str(e)[:100]}")
                failed_count += 1
                
        except Exception as e:
            print(f"  ✗ Unexpected error: {str(e)[:100]}")
            traceback.print_exc()
            failed_count += 1
        
        # Progress update every 10 tokens
        if i % 10 == 0:
            elapsed = time.time() - start_time
            rate = i / elapsed
            remaining = (len(tokens_to_analyze) - i) / rate
            print(f"\n⏱️  Progress: {i}/{len(tokens_to_analyze)} ({i/len(tokens_to_analyze)*100:.1f}%)")
            print(f"   Rate: {rate:.1f} tokens/sec")
            print(f"   Est. remaining: {remaining/60:.1f} minutes")
        
        # Small delay between requests
        time.sleep(2)
    
    # Final summary
    elapsed = time.time() - start_time
    print("\n" + "=" * 80)
    print("BATCH ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"Analyzed: {analyzed_count} tokens")
    print(f"Failed: {failed_count} tokens")
    print(f"Time: {elapsed/60:.1f} minutes")
    print(f"Rate: {analyzed_count/elapsed:.2f} tokens/sec")
    
    # Show statistics
    conn = sqlite3.connect('token_discovery_analysis.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            AVG(total_score) as avg_score,
            SUM(CASE WHEN proceed_to_stage_2 = 1 THEN 1 ELSE 0 END) as stage2_count
        FROM website_analysis
    """)
    stats = cursor.fetchone()
    conn.close()
    
    print(f"\nDatabase Statistics:")
    print(f"  Total in DB: {stats[0]} tokens")
    print(f"  Average Score: {stats[1]:.1f}/21")
    print(f"  Stage 2 Qualified: {stats[2]} ({stats[2]/stats[0]*100:.1f}%)")

def main():
    print("Token Discovery Batch Website Analysis")
    print("=" * 80)
    analyze_tokens()
    print("\n✓ Analysis complete! View results at http://localhost:5007")

if __name__ == "__main__":
    main()