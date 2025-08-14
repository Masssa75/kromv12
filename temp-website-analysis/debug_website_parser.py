#!/usr/bin/env python3
"""
Debug version - see exactly what's happening with website parsing
"""

import requests
from bs4 import BeautifulSoup

def debug_parse(website_url, contract_address):
    """
    Debug what's actually on the website
    """
    print(f"\n{'='*60}")
    print(f"DEBUGGING: {website_url}")
    print(f"Looking for: {contract_address}")
    print("="*60)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(website_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        html = response.text
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text()
        
        print(f"\nPage size: {len(html)} bytes")
        print(f"Text size: {len(text)} chars")
        
        # Search for contract in different forms
        contract_lower = contract_address.lower()
        contract_no_0x = contract_lower.replace('0x', '')
        
        # Check if contract appears anywhere
        if contract_lower in html.lower():
            print(f"✅ Found exact contract in HTML!")
            # Find where it appears
            pos = html.lower().find(contract_lower)
            snippet = html[max(0, pos-50):min(len(html), pos+100)]
            print(f"Context: ...{snippet}...")
        elif contract_no_0x in html.lower():
            print(f"✅ Found contract without 0x in HTML!")
            pos = html.lower().find(contract_no_0x)
            snippet = html[max(0, pos-50):min(len(html), pos+100)]
            print(f"Context: ...{snippet}...")
        else:
            print(f"❌ Contract NOT found in HTML")
            
        # Check text content
        if contract_lower in text.lower():
            print(f"✅ Found in text content")
        elif contract_no_0x in text.lower():
            print(f"✅ Found without 0x in text")
        else:
            print(f"❌ Not in visible text")
            
        # Look for common patterns
        print("\nSearching for common patterns...")
        
        # Check for "contract" word near addresses
        contract_mentions = soup.find_all(text=lambda text: 'contract' in text.lower() if text else False)
        if contract_mentions:
            print(f"Found {len(contract_mentions)} mentions of 'contract'")
            for mention in contract_mentions[:3]:
                print(f"  - {mention[:100]}")
        
        # Check links to block explorers
        explorer_links = soup.find_all('a', href=lambda href: href and any(
            x in href.lower() for x in ['etherscan', 'basescan', 'bscscan', 'snowtrace', 'polygonscan']
        ) if href else False)
        
        if explorer_links:
            print(f"\nFound {len(explorer_links)} block explorer links:")
            for link in explorer_links[:3]:
                href = link.get('href', '')
                if contract_no_0x in href.lower():
                    print(f"  ✅ CONTRACT IN LINK: {href}")
                else:
                    print(f"  - {href[:100]}")
        
        # Check for copy buttons
        copy_elements = soup.find_all(class_=lambda x: x and 'copy' in str(x).lower())
        if copy_elements:
            print(f"\nFound {len(copy_elements)} copy elements")
            for elem in copy_elements[:3]:
                elem_text = elem.get_text()[:100]
                if elem_text:
                    print(f"  - {elem_text}")
                    
        # Check footer (contracts often in footer)
        footer = soup.find('footer')
        if footer:
            footer_text = footer.get_text()
            if contract_no_0x in footer_text.lower():
                print(f"\n✅ FOUND IN FOOTER!")
                print(f"Footer text: {footer_text[:200]}")
            else:
                print(f"\n❌ Not in footer (footer exists but no contract)")
        else:
            print("\n❌ No footer found")
            
    except Exception as e:
        print(f"❌ Error: {e}")

# Test the problematic ones
test_cases = [
    {
        'name': 'VOCL (should be LEGITIMATE - contract in footer)',
        'website': 'https://vocalad.ai/',
        'contract': '0xfEa2e874C0d06031E65ea7E275070e207c2746Fd'
    },
    {
        'name': 'TREN (should be LEGITIMATE - contract in docs)',
        'website': 'https://www.tren.finance/',
        'contract': '0xa77E22bFAeE006D4f9DC2c20D7D337b05125C282'
    }
]

for test in test_cases:
    print(f"\n{'='*80}")
    print(f"Testing: {test['name']}")
    print("="*80)
    debug_parse(test['website'], test['contract'])