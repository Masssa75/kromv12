#!/usr/bin/env python3
"""
Check TREN docs directly for the contract
"""

from playwright.sync_api import sync_playwright

def check_for_contract(url, contract):
    """
    Load URL and search for contract
    """
    print(f"Checking {url} for contract...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Navigate to the docs
            page.goto(url, wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(3000)
            
            # Get all content
            content = page.content()
            text = page.inner_text('body')
            
            contract_lower = contract.lower()
            contract_no_0x = contract_lower.replace('0x', '')
            
            # Check HTML
            if contract_lower in content.lower():
                print("✅ Found contract in HTML!")
                
                # Find where
                pos = content.lower().find(contract_lower)
                snippet = content[max(0, pos-100):pos+150]
                print(f"Context in HTML: ...{snippet}...")
                return True
                
            elif contract_no_0x in content.lower() and len(contract_no_0x) > 20:
                print("✅ Found contract (without 0x) in HTML!")
                return True
                
            # Check visible text
            if contract_lower in text.lower():
                print("✅ Found contract in visible text!")
                
                # Find where in text
                pos = text.lower().find(contract_lower)
                snippet = text[max(0, pos-50):pos+100]
                print(f"Context: ...{snippet}...")
                return True
                
            print("❌ Contract not found")
            
            # Let's see what IS on the page
            print(f"\nPage title: {page.title()}")
            print(f"Page has {len(text)} characters of text")
            
            # Look for any ethereum addresses
            import re
            eth_addresses = re.findall(r'0x[a-fA-F0-9]{40}', text)
            if eth_addresses:
                print(f"Found {len(eth_addresses)} Ethereum addresses on page:")
                for addr in eth_addresses[:3]:
                    print(f"  - {addr}")
                    if addr.lower() == contract_lower:
                        print("    ^ This is our contract!")
            else:
                print("No Ethereum addresses found on page")
                
        except Exception as e:
            print(f"Error: {e}")
            return False
        finally:
            browser.close()
    
    return False

# TREN contract
contract = '0xa77E22bFAeE006D4f9DC2c20D7D337b05125C282'

print("="*60)
print("CHECKING TREN DOCUMENTATION")
print("="*60)
print(f"Contract: {contract}")
print()

# Try different possible URLs
urls_to_try = [
    'https://docs.tren.finance',
    'https://docs.tren.finance/contracts',
    'https://docs.tren.finance/addresses',
    'https://docs.tren.finance/developers',
    'https://docs.tren.finance/smart-contracts',
]

found = False
for url in urls_to_try:
    print(f"\n{'='*40}")
    if check_for_contract(url, contract):
        found = True
        print(f"\n✅ SUCCESS! Contract found at: {url}")
        break
    print()

if not found:
    print("\n❌ Contract not found in any of the checked URLs")
    print("\nThe contract might be:")
    print("1. On a different page in the docs")
    print("2. Behind authentication")
    print("3. Loaded dynamically after user interaction")
    print("4. Or TREN might not have published their contract address yet")