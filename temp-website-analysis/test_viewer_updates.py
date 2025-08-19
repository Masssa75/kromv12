#!/usr/bin/env python3
"""Test if the viewer shows contract addresses and DexScreener links"""

from playwright.sync_api import sync_playwright
import time

def test_viewer():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        # Navigate to the viewer
        page.goto("http://localhost:5007")
        
        # Wait for results to load
        page.wait_for_selector(".result-item", timeout=5000)
        
        # Take a screenshot
        page.screenshot(path="viewer_with_contracts.png")
        
        # Check if contract addresses are visible
        contract_elements = page.query_selector_all("span[style*='monospace']")
        print(f"Found {len(contract_elements)} contract address elements")
        
        # Check if DexScreener links are visible
        dex_links = page.query_selector_all("a[href*='dexscreener.com']")
        print(f"Found {len(dex_links)} DexScreener links")
        
        # Get the first few results to check
        results = page.query_selector_all(".result-item")
        print(f"\nTotal results visible: {len(results)}")
        
        # Check first result in detail
        if results:
            first_result = results[0]
            
            # Get ticker
            ticker = first_result.query_selector(".ticker-name")
            if ticker:
                print(f"\nFirst token: {ticker.inner_text()}")
            
            # Check for contract in the first result
            metadata_rows = first_result.query_selector_all(".metadata-row")
            print(f"Metadata rows in first result: {len(metadata_rows)}")
            
            for i, row in enumerate(metadata_rows):
                print(f"  Row {i+1}: {row.inner_text()[:100]}")
        
        # Click on first result to open modal
        if results:
            results[0].click()
            time.sleep(1)
            
            # Check modal content
            modal = page.query_selector("#modalBody")
            if modal:
                modal_text = modal.inner_text()
                if "Contract:" in modal_text:
                    print("\n✓ Contract address found in modal")
                if "DexScreener:" in modal_text:
                    print("✓ DexScreener link found in modal")
                
                # Take screenshot of modal
                page.screenshot(path="viewer_modal_with_contract.png")
        
        time.sleep(3)
        browser.close()

if __name__ == "__main__":
    test_viewer()