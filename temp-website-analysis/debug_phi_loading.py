#!/usr/bin/env python3
"""
Debug PHI website loading issue
"""
from playwright.sync_api import sync_playwright
import time

def debug_phi():
    url = "https://www.phiprotocol.ai"
    
    print(f"Debugging {url} loading issue")
    print("="*60)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Show browser
        page = browser.new_page()
        
        # Navigate
        print("1. Initial navigation...")
        page.goto(url, wait_until='commit', timeout=30000)
        
        # Check content at different stages
        for i in range(5):
            time.sleep(2)
            content = page.evaluate("() => document.body ? document.body.innerText : ''")
            print(f"\n{i*2} seconds: {len(content)} chars")
            print(f"Preview: {content[:200]}...")
            
            # Check for loading indicators
            loading = page.query_selector_all('[class*="load"], [class*="Load"], [class*="spinner"], [class*="progress"]')
            if loading:
                print(f"   Loading elements found: {len(loading)}")
        
        # Wait for specific content to appear
        print("\n2. Waiting for content to load...")
        try:
            # Wait for any substantial text
            page.wait_for_function(
                "() => document.body && document.body.innerText.length > 500",
                timeout=15000
            )
            print("   ✅ Content loaded!")
        except:
            print("   ❌ Timeout waiting for content")
        
        # Final content
        final_content = page.evaluate("() => document.body ? document.body.innerText : ''")
        print(f"\n3. Final content: {len(final_content)} chars")
        print(f"First 500 chars:\n{final_content[:500]}")
        
        # Take screenshots
        page.screenshot(path='phi_initial.png')
        print("\n4. Screenshot saved to phi_initial.png")
        
        # Scroll to trigger any lazy loading
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(3000)
        
        page.screenshot(path='phi_after_scroll.png')
        print("5. Screenshot after scroll saved to phi_after_scroll.png")
        
        browser.close()

if __name__ == "__main__":
    debug_phi()