#!/usr/bin/env python3
"""
Simple screenshot taker for DexScreener page
"""
import os
import sys

# Add script to run playwright
script = """
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.set_viewport_size({"width": 1440, "height": 900})
    
    # Load page
    page.goto('http://localhost:5001/dexscreener', wait_until='networkidle')
    page.wait_for_timeout(3000)
    
    # Take screenshot
    page.screenshot(path='dexscreener-initial.png', full_page=True)
    print("Saved: dexscreener-initial.png")
    
    # Click refresh
    page.click('button:has-text("Refresh Signals")')
    page.wait_for_timeout(5000)
    
    # Take screenshot after refresh
    page.screenshot(path='dexscreener-after-refresh.png', full_page=True)
    print("Saved: dexscreener-after-refresh.png")
    
    # Count categories
    categories = page.query_selector_all('.signal-category')
    print(f"Found {len(categories)} categories")
    
    for i, cat in enumerate(categories):
        tokens = cat.query_selector_all('.token-card')
        title = cat.query_selector('h2')
        title_text = title.text_content() if title else f"Category {i}"
        print(f"{title_text}: {len(tokens)} tokens")
    
    browser.close()
"""

# Write and execute
with open('_playwright_test.py', 'w') as f:
    f.write(script)

os.system(f"{sys.executable} _playwright_test.py")
os.remove('_playwright_test.py')