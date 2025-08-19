#!/usr/bin/env python3
"""
Capture UI results with Playwright
"""
from playwright.sync_api import sync_playwright
import time

def capture_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Show browser
        page = browser.new_page()
        
        # Navigate to the UI
        page.goto('http://localhost:5006', wait_until='networkidle')
        page.wait_for_timeout(3000)
        
        # Take a screenshot
        page.screenshot(path='ui_with_results.png', full_page=True)
        print("Screenshot saved to ui_with_results.png")
        
        # Count results
        result_count = page.locator('.result-card').count()
        print(f"Found {result_count} results in the UI")
        
        # Click on a high-scoring one to show the modal
        if result_count > 0:
            # Find LIQUID (should be near the top)
            liquid_cards = page.locator('.result-card:has-text("LIQUID")')
            if liquid_cards.count() > 0:
                liquid_cards.first.click()
                page.wait_for_timeout(2000)
                page.screenshot(path='ui_with_modal.png', full_page=True)
                print("Screenshot with modal saved to ui_with_modal.png")
        
        browser.close()

if __name__ == "__main__":
    capture_ui()