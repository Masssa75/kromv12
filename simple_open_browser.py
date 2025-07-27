#!/usr/bin/env python3
"""
Simple script to open DexScreener in a browser
"""
try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("❌ Playwright not installed!")
    print("Install with:")
    print("  pip3 install playwright")
    print("  playwright install chromium")
    exit(1)

import time

# Check if server is running
import requests
try:
    requests.get('http://localhost:5001/api/health', timeout=1)
    print("✅ Server is running")
except:
    print("❌ Server not running! Start with:")
    print("  python3 all-in-one-server.py")
    exit(1)

print("\n🎭 Opening DexScreener in browser...")

with sync_playwright() as p:
    # Open visible browser
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    page.set_viewport_size({"width": 1440, "height": 900})
    
    # Go to DexScreener
    print("📍 Loading page...")
    page.goto('http://localhost:5001/dexscreener')
    page.wait_for_timeout(2000)
    
    # Click refresh
    print("🔄 Clicking refresh...")
    page.click('button:has-text("Refresh Signals")')
    page.wait_for_timeout(5000)
    
    # Count tokens
    print("\n📊 Results:")
    categories = page.query_selector_all('.signal-category')
    for cat in categories:
        title = cat.query_selector('h2')
        if title:
            tokens = cat.query_selector_all('.token-card')
            print(f"{title.text_content()}: {len(tokens)} tokens")
    
    print("\n✅ Browser open - interact with it!")
    print("Will close in 30 seconds...")
    time.sleep(30)
    
    browser.close()
    print("👋 Done!")