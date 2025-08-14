#!/usr/bin/env python3
"""
Deep investigation of BASESHAKE token to find where the CA was located
"""

from playwright.sync_api import sync_playwright
import time
import re

def investigate_baseshake():
    """Use Playwright to fetch and analyze the Farcaster page"""
    
    url = "https://farcaster.xyz/barmstrong/0xbdd5e809"
    contract = "0x885a590198e5F0947f4c92DB815cF2a2147980B8"
    
    print("=" * 70)
    print("INVESTIGATING BASESHAKE CONTRACT LOCATION")
    print("=" * 70)
    print(f"URL: {url}")
    print(f"Contract: {contract}")
    print(f"Contract (no 0x): {contract[2:]}")
    print()
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = context.new_page()
        
        try:
            print("Loading page...")
            page.goto(url, wait_until='networkidle', timeout=30000)
            time.sleep(3)  # Let dynamic content load
            
            # Get full page content
            content = page.content()
            
            # Search for contract in various forms
            contract_lower = contract.lower()
            contract_no_prefix = contract[2:].lower()
            
            print("\n" + "=" * 70)
            print("SEARCHING FOR CONTRACT IN PAGE CONTENT")
            print("=" * 70)
            
            # Check if contract appears at all
            if contract_lower in content.lower():
                print("✅ FOUND: Full contract WITH 0x prefix")
                
                # Find all occurrences
                positions = []
                search_text = content.lower()
                start = 0
                while True:
                    pos = search_text.find(contract_lower, start)
                    if pos == -1:
                        break
                    positions.append(pos)
                    start = pos + 1
                
                print(f"Found {len(positions)} occurrence(s)")
                
                # Show context for each occurrence
                for i, pos in enumerate(positions[:5], 1):  # Show first 5
                    print(f"\n--- Occurrence {i} at position {pos} ---")
                    context_start = max(0, pos - 100)
                    context_end = min(len(content), pos + len(contract) + 100)
                    context_text = content[context_start:context_end]
                    
                    # Clean up for display
                    context_text = context_text.replace('\n', ' ').replace('  ', ' ')
                    print(f"Context: ...{context_text}...")
                    
            elif contract_no_prefix in content.lower():
                print("✅ FOUND: Contract WITHOUT 0x prefix")
                
                # Find position
                pos = content.lower().find(contract_no_prefix)
                context_start = max(0, pos - 100)
                context_end = min(len(content), pos + len(contract_no_prefix) + 100)
                context_text = content[context_start:context_end]
                context_text = context_text.replace('\n', ' ').replace('  ', ' ')
                print(f"Context: ...{context_text}...")
            else:
                print("❌ NOT FOUND: Contract not in page content")
            
            # Check visible text only
            print("\n" + "=" * 70)
            print("CHECKING VISIBLE TEXT")
            print("=" * 70)
            
            visible_text = page.inner_text('body')
            if contract_lower in visible_text.lower():
                print("✅ Contract is in VISIBLE text")
                
                # Find line containing contract
                lines = visible_text.split('\n')
                for i, line in enumerate(lines):
                    if contract_lower in line.lower():
                        print(f"\nLine {i}: {line[:150]}...")
                        break
            else:
                print("❌ Contract is NOT in visible text (may be in metadata/hidden)")
            
            # Check for contract in specific elements
            print("\n" + "=" * 70)
            print("CHECKING SPECIFIC ELEMENTS")
            print("=" * 70)
            
            # Check links
            links = page.query_selector_all('a')
            for link in links:
                href = link.get_attribute('href') or ''
                text = link.inner_text() or ''
                if contract_lower in href.lower() or contract_lower in text.lower():
                    print(f"✅ Found in link: href={href[:50]}... text={text[:50]}...")
            
            # Check comments/replies if any
            comments = page.query_selector_all('[class*="comment"], [class*="reply"], [class*="cast"]')
            for i, comment in enumerate(comments[:10]):  # Check first 10
                text = comment.inner_text() or ''
                if contract_lower in text.lower():
                    print(f"✅ Found in comment/reply {i}: {text[:100]}...")
            
            # Check meta tags
            metas = page.query_selector_all('meta')
            for meta in metas:
                content_attr = meta.get_attribute('content') or ''
                if contract_lower in content_attr.lower():
                    name = meta.get_attribute('name') or meta.get_attribute('property') or 'unknown'
                    print(f"✅ Found in meta tag '{name}': {content_attr[:100]}...")
            
            # Save page for manual inspection
            with open('baseshake_page.html', 'w') as f:
                f.write(content)
            print("\n📄 Full page saved to: baseshake_page.html")
            
        except Exception as e:
            print(f"Error: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    investigate_baseshake()