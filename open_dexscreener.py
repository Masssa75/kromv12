from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    # Launch browser in headed mode
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.set_viewport_size({"width": 1440, "height": 900})
    
    # Navigate to DexScreener
    print("Loading http://localhost:5001/dexscreener")
    page.goto('http://localhost:5001/dexscreener', wait_until='networkidle')
    
    # Wait and click refresh
    page.wait_for_timeout(2000)
    page.click('button:has-text("Refresh Signals")')
    page.wait_for_timeout(5000)
    
    # Count tokens
    categories = page.query_selector_all('.signal-category')
    for cat in categories:
        title = cat.query_selector('h2').text_content()
        tokens = cat.query_selector_all('.token-card')
        print(f"{title}: {len(tokens)} tokens")
    
    # Keep open for 30 seconds
    print("Browser will stay open for 30 seconds...")
    time.sleep(30)
    browser.close()