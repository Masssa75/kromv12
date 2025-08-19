#!/usr/bin/env python3
"""
Take a screenshot of the UI
"""
from playwright.sync_api import sync_playwright

def screenshot_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Show browser
        page = browser.new_page()
        
        # Navigate to the UI
        page.goto('http://localhost:5006', wait_until='networkidle')
        page.wait_for_timeout(2000)
        
        # Take a screenshot
        page.screenshot(path='ui_current_results.png', full_page=True)
        print("Screenshot saved to ui_current_results.png")
        
        # Get the page title and some content
        title = page.title()
        print(f"Page title: {title}")
        
        # Count items with the right selector
        items = page.query_selector_all('.result-card')
        print(f"Found {len(items)} result cards")
        
        browser.close()

if __name__ == "__main__":
    screenshot_ui()