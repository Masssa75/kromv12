#!/usr/bin/env python3
"""
Check the CORRECT TREN docs URL for contract
"""

from playwright.sync_api import sync_playwright
import re

def check_tren_contracts_page():
    """
    Check the actual contract addresses page
    """
    url = 'https://docs.tren.finance/resources/contract-addresses'
    contract = '0xa77E22bFAeE006D4f9DC2c20D7D337b05125C282'
    
    print("="*60)
    print("CHECKING TREN CONTRACT ADDRESSES PAGE")
    print("="*60)
    print(f"URL: {url}")
    print(f"Looking for: {contract}")
    print()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Navigate to the page
            print("Loading page...")
            page.goto(url, wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(3000)
            
            # Get content
            content = page.content()
            text = page.inner_text('body')
            
            print(f"Page loaded: {len(text)} characters")
            print(f"Page title: {page.title()}")
            print()
            
            contract_lower = contract.lower()
            contract_no_0x = contract_lower.replace('0x', '')
            
            # Search for the contract
            if contract_lower in content.lower():
                print("✅ FOUND! Contract is in the HTML")
                
                # Find context
                pos = content.lower().find(contract_lower)
                # Extract surrounding text, cleaning HTML
                snippet_raw = content[max(0, pos-200):pos+200]
                snippet = re.sub(r'<[^>]+>', ' ', snippet_raw)
                snippet = ' '.join(snippet.split())  # Clean whitespace
                print(f"\nContext: ...{snippet}...")
                
            elif contract_no_0x in content.lower() and len(contract_no_0x) > 20:
                print("✅ FOUND! Contract is in the HTML (without 0x prefix)")
            else:
                print("❌ Contract NOT found in HTML")
            
            # Check visible text
            if contract_lower in text.lower():
                print("\n✅ Contract also visible in page text")
                
                # Find where in text
                lines = text.split('\n')
                for i, line in enumerate(lines):
                    if contract_lower in line.lower():
                        print(f"\nFound on line {i+1}:")
                        # Show surrounding lines
                        for j in range(max(0, i-2), min(len(lines), i+3)):
                            prefix = ">>> " if j == i else "    "
                            print(f"{prefix}{lines[j][:100]}")
                        break
            
            # Look for ALL addresses on the page
            print("\n" + "="*40)
            print("All Ethereum addresses found on page:")
            eth_addresses = re.findall(r'0x[a-fA-F0-9]{40}', text)
            
            if eth_addresses:
                for addr in eth_addresses:
                    if addr.lower() == contract_lower:
                        print(f"✅ {addr} <- THIS IS OUR CONTRACT!")
                    else:
                        print(f"   {addr}")
            else:
                print("No Ethereum addresses found")
                
            # Try to find what IS on the page
            if not eth_addresses:
                print("\nFirst 500 characters of page text:")
                print("-"*40)
                print(text[:500])
                
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

check_tren_contracts_page()