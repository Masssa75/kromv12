#!/usr/bin/env python3
"""Test the UI with Playwright"""

from playwright.sync_api import sync_playwright
import time

def test_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("Opening UI...")
        page.goto("http://localhost:5005")
        
        # Wait for page to load
        page.wait_for_selector('.results-list', timeout=10000)
        
        # Wait a bit for the AJAX to load
        time.sleep(2)
        
        # Check if any results are loaded
        results = page.query_selector_all('.result-item')
        print(f"Found {len(results)} result items")
        
        # If no results, check the content
        if len(results) == 0:
            content = page.query_selector('#results')
            if content:
                print(f"Results div content: {content.inner_text()[:200]}")
            
            # Check console for errors
            page.evaluate("console.log('Debug: Checking for errors')")
            
            # Try to manually load results
            try:
                response = page.evaluate("""
                    fetch('/api/results')
                        .then(r => r.json())
                        .then(data => data.count)
                        .catch(e => 'Error: ' + e.message)
                """)
                print(f"Manual API call result: {response}")
            except Exception as e:
                print(f"Manual API call failed: {e}")
        
        if results:
            # Click on the first result
            print("Clicking on first result...")
            results[0].click()
            
            # Wait for modal to appear
            try:
                modal = page.wait_for_selector('#detailModal', timeout=3000)
                if modal:
                    print("✅ Modal opened successfully!")
                    
                    # Check if modal content is loaded
                    modal_body = page.query_selector('#modalBody')
                    if modal_body:
                        content = modal_body.inner_text()
                        print(f"Modal content length: {len(content)} chars")
                        if len(content) > 0:
                            print("✅ Modal has content")
                        else:
                            print("❌ Modal is empty")
                    else:
                        print("❌ Modal body not found")
                else:
                    print("❌ Modal did not appear")
            except Exception as e:
                print(f"❌ Error waiting for modal: {e}")
                
                # Check console errors
                print("\nChecking for JavaScript errors...")
                # Get the page's console messages
                page.evaluate("console.log('Test log message')")
        else:
            print("❌ No results found")
            
        # Take a screenshot
        page.screenshot(path='/Users/marcschwyn/Desktop/projects/KROMV12/temp-website-analysis/ui_test.png')
        print("Screenshot saved to ui_test.png")
        
        # Keep browser open for manual inspection
        print("Browser will stay open for 10 seconds...")
        time.sleep(10)
        
        browser.close()

if __name__ == "__main__":
    test_ui()