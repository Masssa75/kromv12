#!/usr/bin/env python3
"""
Test improved parsing on problematic sites
"""
from comprehensive_website_analyzer import ComprehensiveWebsiteAnalyzer

def test_sites():
    analyzer = ComprehensiveWebsiteAnalyzer()
    
    test_cases = [
        ("PHI", "https://www.phiprotocol.ai"),
        ("CREATOR", "https://creatordao.com"),
        ("VIRUS", "https://www.pndm.org/")
    ]
    
    for ticker, url in test_cases:
        print(f"\n{'='*60}")
        print(f"Testing {ticker}: {url}")
        print(f"{'='*60}")
        
        # Parse with improved waiting
        parsed_data = analyzer.parse_website_with_playwright(url)
        parsed_data['ticker'] = ticker
        
        if parsed_data['success']:
            content = parsed_data['content'].get('text', '')
            print(f"✅ Parsed successfully")
            print(f"   Content: {len(content)} chars")
            print(f"   Preview: {content[:200]}...")
            
            # Check for key content
            if ticker == "PHI":
                if "AI Liquidity Layer" in content or "Phi Protocol" in content:
                    print(f"   ✅ Found Phi Protocol content!")
                else:
                    print(f"   ❌ Missing Phi Protocol content")
            
            elif ticker == "CREATOR":
                if "Kong" in content or "4 million" in content:
                    print(f"   ✅ Found team info (Kong, 4M subscribers)!")
                if "$50" in content or "50+ million" in content:
                    print(f"   ✅ Found revenue info ($50M)!")
            
            elif ticker == "VIRUS":
                print(f"   Checking for substantial content beyond loading screen...")
                if len(content) > 500:
                    print(f"   ✅ Has substantial content")
            
            # Analyze with AI
            models = [("moonshotai/kimi-k2", "Kimi K2")]
            results = analyzer.analyze_with_models(parsed_data, models_to_test=models)
            
            if results and len(results) > 0:
                score = results[0]['analysis'].get('total_score', 0)
                exceptional = results[0]['analysis'].get('exceptional_signals', [])
                
                print(f"\n📊 AI Analysis:")
                print(f"   Score: {score}/21")
                if exceptional:
                    print(f"   Exceptional signals found:")
                    for signal in exceptional:
                        print(f"   - {signal}")
        else:
            print(f"❌ Parse failed: {parsed_data.get('error')}")

if __name__ == "__main__":
    test_sites()