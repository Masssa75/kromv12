#!/usr/bin/env python3
"""
Test the top 10 tokens with fixed timeout settings
"""
from comprehensive_website_analyzer import ComprehensiveWebsiteAnalyzer
import time

# Top 10 tokens
tokens = [
    ("NKP", "https://nonkyotoprotocol.com/", 2066642),
    ("PAWSE", "https://pawse.xyz/", 1877725),  # SSL issue
    ("$COLLAT", "https://www.collaterize.com/", 1709647),
    ("VIBE", "https://jup.ag/studio/DFVeSFxNohR5CVuReaXSz6rGuJ62LsKhxFpWsDbbjups", 752374),
    ("M0N3Y", "https://mnply.money", 735883),
    ("STM", "https://steam22.io/", 614127),
    ("LIQUID", "https://liquidagent.ai", 576762),
    ("T", "https://talos.is/", 556788),
    ("LITTLEGUY", "https://hesjustalittleguy.com/", 449320),
    ("YEE", "https://yeetoken.vip", 447911)
]

def main():
    print("\n" + "="*80)
    print("TESTING TOP 10 TOKENS WITH FIXED TIMEOUT")
    print("="*80)
    
    analyzer = ComprehensiveWebsiteAnalyzer()
    models = [("moonshotai/kimi-k2", "Kimi K2")]
    
    successful = 0
    failed = 0
    high_scores = []
    
    for ticker, url, liquidity in tokens:
        print(f"\n[{ticker}] {url}")
        print(f"  💧 Liquidity: ${liquidity:,}")
        
        try:
            # Parse website
            parsed_data = analyzer.parse_website_with_playwright(url)
            parsed_data['ticker'] = ticker
            
            if parsed_data['success']:
                # Analyze
                results = analyzer.analyze_with_models(parsed_data, models_to_test=models)
                successful += 1
                
                # Get score from results
                if results and len(results) > 0:
                    score = results[0]['analysis'].get('total_score', 0)
                    tier = results[0]['analysis'].get('tier', 'UNKNOWN')
                    signals = results[0]['analysis'].get('exceptional_signals', [])
                    
                    if score >= 10:
                        high_scores.append((ticker, url, score, tier, signals))
                    
                    print(f"  ✅ Analysis complete: {score}/21 ({tier})")
                    if signals:
                        print(f"  🌟 Exceptional signals: {signals[0][:100] if signals else 'None'}")
            else:
                failed += 1
                print(f"  ❌ Parse failed: {parsed_data.get('error', 'Unknown')[:100]}")
                
        except Exception as e:
            failed += 1
            print(f"  ❌ Error: {str(e)[:100]}")
        
        time.sleep(2)  # Be respectful
    
    print(f"\n" + "="*80)
    print(f"SUMMARY")
    print(f"="*80)
    print(f"✅ Successful: {successful}/10")
    print(f"❌ Failed: {failed}/10")
    
    if high_scores:
        print(f"\n🏆 HIGH SCORING TOKENS (>= 10/21):")
        for ticker, url, score, tier, signals in high_scores:
            print(f"  {ticker}: {score}/21 ({tier})")
            if signals:
                print(f"    Signal: {signals[0][:80]}")
    else:
        print(f"\n📊 No tokens scored >= 10/21 (most crypto is low quality)")

if __name__ == "__main__":
    main()