#!/usr/bin/env python3
"""
Check the UI results with Playwright
"""
from playwright.sync_api import sync_playwright

def check_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Navigate to the UI
        page.goto('http://localhost:5006', wait_until='domcontentloaded')
        page.wait_for_timeout(2000)
        
        # Take a screenshot
        page.screenshot(path='ui_results.png')
        
        # Count the results
        results = page.query_selector_all('.result-item')
        print(f"Found {len(results)} results in the UI")
        
        # Get the text content of each result
        for i, result in enumerate(results[:10], 1):  # Show first 10
            ticker = result.query_selector('.ticker-symbol')
            score = result.query_selector('.score')
            tier = result.query_selector('.tier-badge')
            
            ticker_text = ticker.inner_text() if ticker else 'N/A'
            score_text = score.inner_text() if score else 'N/A'
            tier_text = tier.inner_text() if tier else 'N/A'
            
            print(f"{i}. {ticker_text}: {score_text} ({tier_text})")
        
        browser.close()

if __name__ == "__main__":
    check_ui()