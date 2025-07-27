#!/usr/bin/env python3
"""
Playwright test to verify DexScreener fixes
This will take screenshots and show exactly what's displayed
"""
import subprocess
import sys

# First, try to import playwright
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("Installing playwright...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    from playwright.sync_api import sync_playwright

import time
from datetime import datetime

def test_dexscreener_with_playwright():
    """Run Playwright test and take screenshots"""
    
    print("🎭 Starting Playwright Test for DexScreener")
    print("=" * 60)
    
    with sync_playwright() as p:
        # Launch browser in headless mode
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Set viewport
        page.set_viewport_size({"width": 1440, "height": 900})
        
        try:
            # Navigate to DexScreener page
            print("\n1. Loading DexScreener page...")
            page.goto('http://localhost:5001/dexscreener', wait_until='networkidle')
            
            # Wait for initial load
            page.wait_for_timeout(3000)
            
            # Take initial screenshot
            timestamp = datetime.now().strftime('%H%M%S')
            page.screenshot(path=f'test-before-refresh-{timestamp}.png', full_page=True)
            print(f"✅ Screenshot saved: test-before-refresh-{timestamp}.png")
            
            # Get initial counts
            summary_text = page.text_content('#summary')
            print(f"\n2. Initial state: {summary_text}")
            
            # Click refresh button
            print("\n3. Clicking refresh button...")
            page.click('button:has-text("Refresh Signals")')
            
            # Wait for data to load
            page.wait_for_timeout(5000)
            
            # Take after-refresh screenshot
            page.screenshot(path=f'test-after-refresh-{timestamp}.png', full_page=True)
            print(f"✅ Screenshot saved: test-after-refresh-{timestamp}.png")
            
            # Count tokens in each category
            print("\n4. Counting tokens in each category...")
            
            categories = page.query_selector_all('.signal-category')
            print(f"   Found {len(categories)} categories")
            
            category_results = []
            for i, category in enumerate(categories):
                # Get category title
                title = category.query_selector('h2')
                title_text = title.text_content() if title else "Unknown"
                
                # Count token cards
                token_cards = category.query_selector_all('.token-card')
                count = len(token_cards)
                
                # Take category screenshot
                category.screenshot(path=f'test-category-{i}-{timestamp}.png')
                
                category_results.append({
                    'title': title_text.strip(),
                    'count': count
                })
                
                print(f"   {title_text}: {count} tokens")
                
                # Get first token if any
                if token_cards and count > 0:
                    first_token = token_cards[0]
                    symbol = first_token.query_selector('.token-symbol')
                    if symbol:
                        print(f"     First token: {symbol.text_content()}")
            
            # Get updated summary
            updated_summary = page.text_content('#summary')
            print(f"\n5. Updated summary: {updated_summary}")
            
            # Check for errors
            error_elements = page.query_selector_all(':text("Error")')
            if error_elements:
                print("\n⚠️  Errors found on page:")
                for error in error_elements:
                    print(f"   - {error.text_content()}")
            
            # Summary
            print("\n" + "=" * 60)
            print("📊 TEST RESULTS:")
            for result in category_results:
                status = "✅" if result['count'] > 0 else "❌"
                print(f"{status} {result['title']}: {result['count']} tokens")
            
            print(f"\n📸 Screenshots saved:")
            print(f"- test-before-refresh-{timestamp}.png")
            print(f"- test-after-refresh-{timestamp}.png")
            print(f"- test-category-0-{timestamp}.png (and others)")
            
            # Return results
            return {
                'success': True,
                'categories': category_results,
                'timestamp': timestamp
            }
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            page.screenshot(path=f'test-error-{timestamp}.png')
            print(f"Error screenshot: test-error-{timestamp}.png")
            return {
                'success': False,
                'error': str(e)
            }
        
        finally:
            browser.close()

if __name__ == "__main__":
    # Check if server is running
    import requests
    try:
        response = requests.get('http://localhost:5001/api/health', timeout=2)
        if response.status_code != 200:
            print("❌ Server not responding properly")
            sys.exit(1)
    except:
        print("❌ Server is not running!")
        print("Please run: python3 all-in-one-server.py")
        sys.exit(1)
    
    # Run the test
    results = test_dexscreener_with_playwright()
    
    if results['success']:
        print("\n✅ Test completed successfully!")
        print("Check the screenshots to see what's displayed.")
    else:
        print("\n❌ Test failed!")
        print(f"Error: {results.get('error', 'Unknown error')}")