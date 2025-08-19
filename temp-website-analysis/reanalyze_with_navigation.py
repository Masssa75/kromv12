#!/usr/bin/env python3
"""
Re-analyze websites to capture navigation data
"""
from comprehensive_website_analyzer import ComprehensiveWebsiteAnalyzer

def main():
    analyzer = ComprehensiveWebsiteAnalyzer()
    
    # Re-analyze the 4 websites we already have
    websites = [
        "https://tharwa.finance/",
        "https://www.graphai.tech/",
        "https://www.buildon.online",
        "https://www.blockstreet.xyz/"
    ]
    
    print("\n" + "="*60)
    print("RE-ANALYZING WITH NAVIGATION TRACKING")
    print("="*60)
    
    for url in websites:
        print(f"\n🔄 Re-analyzing: {url}")
        result = analyzer.analyze_single_website(url)
        
        if result and result['parsed_data'].get('navigation'):
            nav = result['parsed_data']['navigation']
            print(f"  ✅ Navigation data captured:")
            print(f"     - Total links: {len(nav.get('all_links', []))}")
            print(f"     - Parsed sections: {len(nav.get('parsed_sections', []))}")
            print(f"     - High priority: {len([l for l in nav.get('all_links', []) if l.get('priority') == 'high'])}")
    
    print("\n✅ Re-analysis complete! Refresh the viewer to see navigation data.")

if __name__ == "__main__":
    main()