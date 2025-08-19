#!/usr/bin/env python3
"""Test the UI to see what's being displayed"""
from playwright.sync_api import sync_playwright
import time

def test_ui():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Set to False to see browser
        page = browser.new_page()
        
        # Navigate to the UI
        page.goto('http://localhost:5005')
        
        # Wait for content to load
        page.wait_for_timeout(3000)
        
        # Take a screenshot
        page.screenshot(path='ui_screenshot.png')
        print("📸 Screenshot saved as ui_screenshot.png")
        
        # Get all the ticker/name elements
        ticker_elements = page.query_selector_all('.ticker-badge')
        
        print(f"\n🔍 Found {len(ticker_elements)} ticker elements")
        
        # If no ticker-badge class, try other selectors
        if len(ticker_elements) == 0:
            # Try to find all text content in cards
            cards = page.query_selector_all('.analysis-card')
            print(f"\n📦 Found {len(cards)} analysis cards")
            
            for i, card in enumerate(cards[:5], 1):
                text = card.inner_text()
                lines = text.split('\n')
                print(f"\nCard {i}:")
                for line in lines[:3]:  # First 3 lines
                    print(f"  {line}")
        
        # Get the raw HTML to debug
        html = page.content()
        
        # Search for "N/A" in the HTML
        na_count = html.count('N/A')
        print(f"\n⚠️  Found 'N/A' {na_count} times in the HTML")
        
        # Check the API response
        api_response = page.evaluate("""
            fetch('/api/comprehensive')
                .then(response => response.json())
                .then(data => data)
        """)
        
        time.sleep(2)
        
        # Try to get API data directly
        page.goto('http://localhost:5005/api/comprehensive')
        api_text = page.inner_text('body')
        
        # Check if ticker field exists in API
        if 'ticker' in api_text:
            print("\n✅ API response contains 'ticker' field")
        else:
            print("\n❌ API response does NOT contain 'ticker' field")
            
        # Count how many times each ticker appears
        import json
        try:
            api_data = json.loads(api_text)
            tickers = [item.get('ticker', 'NOT_FOUND') for item in api_data]
            print(f"\n📊 Tickers in API response:")
            for ticker in tickers[:10]:
                print(f"  - {ticker}")
        except:
            print("\n❌ Could not parse API response as JSON")
        
        browser.close()

if __name__ == "__main__":
    test_ui()