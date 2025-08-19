#!/usr/bin/env python3
"""
Test smart loading detection
"""
from comprehensive_website_analyzer import ComprehensiveWebsiteAnalyzer

def test_loading_sites():
    analyzer = ComprehensiveWebsiteAnalyzer()
    
    # Sites known to have loading screens
    loading_sites = [
        ("PHI", "https://www.phiprotocol.ai"),
        ("VIRUS", "https://www.pndm.org/")
    ]
    
    for ticker, url in loading_sites:
        print(f"\n{'='*60}")
        print(f"Testing {ticker}: {url}")
        print(f"{'='*60}")
        
        parsed_data = analyzer.parse_website_with_playwright(url)
        
        if parsed_data['success']:
            content = parsed_data['content'].get('text', '')
            print(f"✅ Final content: {len(content)} chars")
            print(f"   Preview: {content[:150]}...")
        else:
            print(f"❌ Parse failed")

if __name__ == "__main__":
    test_loading_sites()