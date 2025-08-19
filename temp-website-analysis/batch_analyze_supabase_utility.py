#!/usr/bin/env python3
"""
Batch analyze utility tokens from Supabase using Kimi K2
Stores results in local website_analysis_new.db
"""
import requests
import sqlite3
import time
from datetime import datetime
from comprehensive_website_analyzer import ComprehensiveWebsiteAnalyzer

def get_utility_tokens_from_supabase():
    """Fetch all utility tokens from Supabase"""
    url = 'https://eucfoommxxvqmmwdbkdv.supabase.co'
    service_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Ria2R2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzU2Mjg4MSwiZXhwIjoyMDYzMTM4ODgxfQ.VcC7Bp3zMFYor3eVDonoG7BuS7AavemQnSOhrWcY5Y4'
    
    headers = {
        'apikey': service_key,
        'Authorization': f'Bearer {service_key}'
    }
    
    # Get tokens where either AI says 'utility'
    print("  Making request to Supabase...")
    response = requests.get(
        f'{url}/rest/v1/crypto_calls',
        headers=headers,
        params={
            'select': 'ticker,website_url,liquidity_usd,analysis_token_type,x_analysis_token_type',
            'is_invalidated': 'eq.false',
            'or': '(analysis_token_type.eq.utility,x_analysis_token_type.eq.utility)',
            'website_url': 'not.is.null',
            'order': 'liquidity_usd.desc.nullsfirst',
            'limit': '1000'
        },
        timeout=30
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Error fetching from Supabase: {response.status_code}')
        return []

def get_already_analyzed():
    """Get list of already analyzed websites from local DB"""
    conn = sqlite3.connect('website_analysis_new.db')
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT url FROM website_analysis")
    analyzed = set(row[0] for row in cursor.fetchall())
    conn.close()
    
    # Normalize URLs for comparison
    normalized = set()
    for url in analyzed:
        normalized.add(url)
        # Add variations
        if url.startswith('https://www.'):
            normalized.add(url.replace('https://www.', 'https://'))
        elif url.startswith('https://'):
            normalized.add(url.replace('https://', 'https://www.'))
    
    return normalized

def normalize_url(url):
    """Normalize URL for comparison"""
    return url.replace('https://www.', 'https://').replace('http://www.', 'http://')

def main():
    print("\n" + "="*80)
    print("SUPABASE UTILITY TOKEN BATCH ANALYSIS - KIMI K2")
    print("="*80)
    
    # Get tokens from Supabase
    print("\n📡 Fetching utility tokens from Supabase...")
    tokens = get_utility_tokens_from_supabase()
    
    # Get unique websites
    unique_websites = {}
    for token in tokens:
        if token.get('website_url'):
            url = token['website_url']
            if url not in unique_websites:
                unique_websites[url] = token
    
    print(f"✅ Found {len(unique_websites)} unique utility token websites")
    
    # Get already analyzed
    analyzed = get_already_analyzed()
    print(f"📊 Already analyzed: {len(analyzed)} websites")
    
    # Filter out analyzed
    to_analyze = []
    for url, token in unique_websites.items():
        if normalize_url(url) not in analyzed:
            to_analyze.append((token['ticker'], url, token.get('liquidity_usd', 0)))
    
    # Sort by liquidity (highest first)
    to_analyze.sort(key=lambda x: x[2] or 0, reverse=True)
    
    # # TEMPORARY: Limit to first 20 for testing
    # to_analyze = to_analyze[:20]
    
    print(f"📋 To analyze: {len(to_analyze)} websites")
    print(f"💰 Estimated cost: ${len(to_analyze) * 0.003:.2f} (Kimi K2)")
    
    if not to_analyze:
        print("\n✅ All utility tokens already analyzed!")
        return
    
    # Show top 10 to analyze
    print("\n🔝 Top 10 by liquidity to analyze:")
    for i, (ticker, url, liq) in enumerate(to_analyze[:10], 1):
        liq_str = f"${int(liq):,}" if liq else "Unknown"
        print(f"  {i}. {ticker}: {liq_str} - {url[:50]}...")
    
    # Auto-start (no confirmation needed)
    print(f"\n⚠️  Ready to analyze {len(to_analyze)} websites")
    print("🚀 Starting in 3 seconds...")
    time.sleep(3)
    
    # Initialize analyzer
    print("\n🚀 Starting batch analysis...")
    analyzer = ComprehensiveWebsiteAnalyzer()
    models = [("moonshotai/kimi-k2", "Kimi K2")]
    
    # Track progress
    successful = 0
    failed = 0
    start_time = time.time()
    
    # Open local DB for checking results
    local_conn = sqlite3.connect('website_analysis_new.db')
    local_cursor = local_conn.cursor()
    
    for i, (ticker, url, liquidity) in enumerate(to_analyze, 1):
        print(f"\n[{i}/{len(to_analyze)}] {ticker}: {url}")
        if liquidity:
            print(f"  💧 Liquidity: ${int(liquidity):,}")
        
        try:
            # Add ticker to parsed data so it gets saved
            parsed_data = analyzer.parse_website_with_playwright(url)
            parsed_data['ticker'] = ticker
            
            if parsed_data['success']:
                # Analyze with Kimi K2
                results = analyzer.analyze_with_models(parsed_data, models_to_test=models)
                
                # Save to database
                analyzer.save_to_database(url, parsed_data, results)
                successful += 1
                
                # Get the score from results
                if results and len(results) > 0:
                    score = results[0]['analysis'].get('total_score', 0)
                    tier = results[0]['analysis'].get('tier', 'UNKNOWN')
                    exceptional = results[0]['analysis'].get('exceptional_signals', [])
                    print(f"  ✅ Analysis complete: {score}/21 ({tier})")
                    if exceptional:
                        print(f"     🌟 {exceptional[0][:80] if exceptional else ''}")
            else:
                failed += 1
                print(f"  ❌ Parse failed: {parsed_data.get('error', 'Unknown error')[:100]}")
                
        except Exception as e:
            failed += 1
            print(f"  ❌ Error: {str(e)[:100]}")
        
        # Progress update every 10 tokens
        if i % 10 == 0:
            elapsed = time.time() - start_time
            rate = i / elapsed
            remaining = (len(to_analyze) - i) / rate if rate > 0 else 0
            
            print(f"\n" + "="*60)
            print(f"📈 PROGRESS UPDATE")
            print(f"  Completed: {i}/{len(to_analyze)} ({i*100/len(to_analyze):.1f}%)")
            print(f"  Success rate: {successful}/{i} ({successful*100/i:.1f}%)")
            print(f"  Time elapsed: {elapsed/60:.1f} min")
            print(f"  Est. remaining: {remaining/60:.1f} min")
            print(f"  Rate: {rate*60:.1f} tokens/min")
            print("="*60)
        
        # Small delay to be respectful
        time.sleep(2)
    
    # Final summary
    total_time = time.time() - start_time
    print(f"\n" + "="*80)
    print(f"✨ BATCH ANALYSIS COMPLETE")
    print(f"="*80)
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"⏱️  Total time: {total_time/60:.1f} minutes")
    print(f"💰 Total cost: ${successful * 0.003:.2f}")
    
    # Get high-scoring tokens
    local_cursor.execute("""
        SELECT url, score, team_members_found
        FROM website_analysis
        WHERE score >= 7
        ORDER BY score DESC, analyzed_at DESC
    """)
    
    high_scorers = local_cursor.fetchall()
    
    if high_scorers:
        print(f"\n🏆 HIGH-SCORING TOKENS (>= 7/10): {len(high_scorers)} found")
        print("-"*60)
        
        for url, score, team in high_scorers[:10]:
            # Try to find ticker from our list
            ticker = next((t for t, u, _ in to_analyze if u == url), ("Unknown", "", 0))[0]
            print(f"  {ticker}: {score}/10, Team: {team}")
            print(f"    {url[:60]}...")
        
        print(f"\n💡 Consider these {len(high_scorers)} tokens for Phase 2 deep analysis")
    
    local_conn.close()
    print("\n✅ Results saved to website_analysis_new.db")
    print("📊 View results at http://localhost:5005")

if __name__ == "__main__":
    main()