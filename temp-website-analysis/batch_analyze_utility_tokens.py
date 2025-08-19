#!/usr/bin/env python3
"""
Batch analyze all utility tokens using only Kimi K2
- 10x cheaper than other models
- Accurate team detection and scoring
"""
import sqlite3
import time
from datetime import datetime
from comprehensive_website_analyzer import ComprehensiveWebsiteAnalyzer

def batch_analyze_tokens():
    # Connect to both databases
    tokens_conn = sqlite3.connect('utility_tokens_ca.db')
    analysis_conn = sqlite3.connect('website_analysis_new.db')
    
    # Get all tokens with websites
    cursor = tokens_conn.cursor()
    cursor.execute("""
        SELECT DISTINCT ticker, website_url, liquidity_usd 
        FROM tokens 
        WHERE website_url IS NOT NULL
        ORDER BY liquidity_usd DESC NULLS LAST
    """)
    
    all_tokens = cursor.fetchall()
    
    # Check what's already analyzed
    analysis_cursor = analysis_conn.cursor()
    analysis_cursor.execute("SELECT DISTINCT url FROM website_analysis")
    analyzed_urls = set(row[0] for row in analysis_cursor.fetchall())
    
    # Normalize URLs for comparison (some have www, some don't)
    normalized_analyzed = set()
    for url in analyzed_urls:
        normalized_analyzed.add(url)
        # Add variations
        if url.startswith('https://www.'):
            normalized_analyzed.add(url.replace('https://www.', 'https://'))
        elif url.startswith('https://'):
            normalized_analyzed.add(url.replace('https://', 'https://www.'))
    
    # Filter out already analyzed
    tokens_to_analyze = [(t, u, l) for t, u, l in all_tokens if u not in normalized_analyzed]
    
    print(f"\n" + "="*80)
    print(f"UTILITY TOKEN BATCH ANALYSIS - KIMI K2 ONLY")
    print(f"="*80)
    print(f"Total tokens: {len(all_tokens)}")
    print(f"Already analyzed: {len(analyzed_urls)}")
    print(f"To analyze: {len(tokens_to_analyze)}")
    print(f"="*80 + "\n")
    
    if not tokens_to_analyze:
        print("✅ All tokens already analyzed!")
        return
    
    # Initialize analyzer
    analyzer = ComprehensiveWebsiteAnalyzer()
    models = [("moonshotai/kimi-k2", "Kimi K2")]
    
    # Track progress
    successful = 0
    failed = 0
    start_time = time.time()
    
    for i, (ticker, url, liquidity) in enumerate(tokens_to_analyze, 1):
        print(f"\n[{i}/{len(tokens_to_analyze)}] Analyzing {ticker} - {url}")
        print(f"  Liquidity: ${liquidity:,.0f}" if liquidity else "  Liquidity: Unknown")
        print("-"*60)
        
        try:
            # Parse website with Playwright
            parsed_data = analyzer.parse_website_with_playwright(url)
            
            if parsed_data['success']:
                # Analyze with Kimi K2
                results = analyzer.analyze_with_models(parsed_data, models_to_test=models)
                successful += 1
                print(f"  ✅ Analysis complete")
                
                # Quick summary from latest result
                analysis_cursor.execute("""
                    SELECT score, team_members_found 
                    FROM website_analysis 
                    WHERE url = ? 
                    ORDER BY analyzed_at DESC 
                    LIMIT 1
                """, (url,))
                
                result = analysis_cursor.fetchone()
                if result:
                    score, team = result
                    tier = "High" if score >= 6 else "Medium" if score >= 4 else "Low"
                    print(f"  📊 Score: {score}/10 ({tier})")
                    print(f"  👥 Team members: {team}")
            else:
                failed += 1
                print(f"  ❌ Failed to parse: {parsed_data.get('error', 'Unknown error')}")
                
        except Exception as e:
            failed += 1
            print(f"  ❌ Error: {str(e)}")
        
        # Progress update every 10 tokens
        if i % 10 == 0:
            elapsed = time.time() - start_time
            rate = i / elapsed
            remaining = (len(tokens_to_analyze) - i) / rate
            print(f"\n📈 Progress: {i}/{len(tokens_to_analyze)} ({i*100/len(tokens_to_analyze):.1f}%)")
            print(f"   Success rate: {successful}/{i} ({successful*100/i:.1f}%)")
            print(f"   Time elapsed: {elapsed/60:.1f} min")
            print(f"   Est. remaining: {remaining/60:.1f} min")
            print(f"   Rate: {rate*60:.1f} tokens/min")
        
        # Small delay to avoid overwhelming services
        time.sleep(2)
    
    # Final summary
    total_time = time.time() - start_time
    print(f"\n" + "="*80)
    print(f"BATCH ANALYSIS COMPLETE")
    print(f"="*80)
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"⏱️  Total time: {total_time/60:.1f} minutes")
    print(f"💰 Estimated cost: ${successful * 0.003:.2f} (Kimi K2 @ ~$0.003/analysis)")
    
    # Show high-scoring tokens for phase 2 consideration
    print(f"\n🏆 HIGH-SCORING TOKENS (>= 7/10):")
    print("-"*60)
    
    analysis_cursor.execute("""
        SELECT DISTINCT url, score, team_members_found, 
               substr(reasoning, 1, 100) as reasoning_preview
        FROM website_analysis
        WHERE score >= 7
        ORDER BY score DESC, team_members_found DESC
    """)
    
    high_scorers = analysis_cursor.fetchall()
    for url, score, team, reasoning in high_scorers:
        # Get ticker from tokens db
        cursor.execute("SELECT ticker FROM tokens WHERE website_url = ?", (url,))
        ticker_result = cursor.fetchone()
        ticker = ticker_result[0] if ticker_result else "Unknown"
        
        print(f"\n📍 {ticker}: {url}")
        print(f"   Score: {score}/10")
        print(f"   Team: {team} members")
        print(f"   Note: {reasoning}...")
    
    if high_scorers:
        print(f"\n💡 Found {len(high_scorers)} high-quality projects for potential Phase 2 deep analysis")
    
    tokens_conn.close()
    analysis_conn.close()

if __name__ == "__main__":
    batch_analyze_tokens()