#!/usr/bin/env python3
"""
Open DexScreener page in a headed browser for visual inspection
"""
from playwright.sync_api import sync_playwright
import time

print("🎭 Opening DexScreener in browser...")
print("=" * 60)

with sync_playwright() as p:
    # Launch browser in headed mode (visible)
    browser = p.chromium.launch(
        headless=False,  # Show the browser window
        args=['--start-maximized']
    )
    
    context = browser.new_context(
        viewport={"width": 1440, "height": 900},
        device_scale_factor=1
    )
    
    page = context.new_page()
    
    # Enable console logging
    page.on("console", lambda msg: print(f"Console: {msg.text}"))
    
    try:
        # Navigate to DexScreener
        print("\n📍 Loading DexScreener page...")
        page.goto('http://localhost:5001/dexscreener', wait_until='networkidle')
        
        # Wait for initial load
        page.wait_for_timeout(2000)
        
        # Get initial state
        summary = page.text_content('#summary')
        print(f"\n📊 Initial state: {summary}")
        
        # Count initial categories
        categories = page.query_selector_all('.signal-category')
        print(f"\n📦 Found {len(categories)} signal categories")
        
        # Click refresh to load data
        print("\n🔄 Clicking refresh button...")
        page.click('button:has-text("Refresh Signals")')
        
        # Wait for data to load
        print("⏳ Waiting for data to load...")
        page.wait_for_timeout(5000)
        
        # Count tokens in each category
        print("\n📊 Results after refresh:")
        for i, category in enumerate(page.query_selector_all('.signal-category')):
            title = category.query_selector('h2')
            title_text = title.text_content() if title else f"Category {i}"
            
            tokens = category.query_selector_all('.token-card')
            print(f"\n{title_text}: {len(tokens)} tokens")
            
            # Show first token if any
            if tokens:
                first_token = tokens[0]
                symbol = first_token.query_selector('.token-symbol')
                if symbol:
                    print(f"  First token: {symbol.text_content()}")
        
        # Get final summary
        final_summary = page.text_content('#summary')
        print(f"\n📊 Final summary: {final_summary}")
        
        print("\n" + "=" * 60)
        print("✅ Browser is open - you can interact with the page")
        print("The page will stay open for 30 seconds...")
        print("Click refresh button to update signals")
        print("=" * 60)
        
        # Keep browser open for inspection
        time.sleep(30)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        # Take error screenshot
        page.screenshot(path='dexscreener-error.png')
        print("Error screenshot saved: dexscreener-error.png")
        
    finally:
        print("\n👋 Closing browser...")
        browser.close()

print("\n✅ Done!")