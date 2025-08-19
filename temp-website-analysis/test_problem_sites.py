#!/usr/bin/env python3
"""
Test the problematic sites to see what's happening
"""
import requests
from playwright.sync_api import sync_playwright
import time

# The sites that had issues
problem_sites = [
    ("NKP", "https://nonkyotoprotocol.com/"),
    ("PAWSE", "https://pawse.xyz/"),
    ("$COLLAT", "https://www.collaterize.com/"),
    ("M0N3Y", "https://mnply.money"),
    ("LIQUID", "https://liquidagent.ai"),
    ("VIBE", "https://jup.ag/studio/DFVeSFxNohR5CVuReaXSz6rGuJ62LsKhxFpWsDbbjups"),
    ("STM", "https://steam22.io/"),
    ("T", "https://talos.is/"),
    ("LITTLEGUY", "https://hesjustalittleguy.com/"),
    ("YEE", "https://yeetoken.vip")
]

def test_basic_access(ticker, url):
    """Test if we can access the site at all"""
    print(f"\n{'='*60}")
    print(f"Testing {ticker}: {url}")
    print(f"{'='*60}")
    
    # First try a simple HTTP request
    print("1. Testing HTTP request...")
    try:
        response = requests.get(url, timeout=10, verify=False, allow_redirects=True)
        print(f"   ✅ Status: {response.status_code}")
        print(f"   ✅ Content length: {len(response.text)} chars")
        if response.history:
            print(f"   ➡️  Redirected: {response.history[-1].status_code} -> {response.url}")
    except Exception as e:
        print(f"   ❌ HTTP Error: {str(e)[:100]}")
    
    # Now try with Playwright
    print("\n2. Testing with Playwright (10s timeout)...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Try with shorter timeout
            page.goto(url, wait_until='domcontentloaded', timeout=10000)
            
            # Wait a bit for JS
            page.wait_for_timeout(2000)
            
            title = page.title()
            content = page.evaluate("() => document.body ? document.body.innerText.length : 0")
            
            print(f"   ✅ Page loaded")
            print(f"   ✅ Title: {title[:50]}")
            print(f"   ✅ Content: {content} chars")
            
            browser.close()
            
    except Exception as e:
        print(f"   ❌ Playwright Error: {str(e)[:150]}")
    
    # Try with different wait strategy
    print("\n3. Testing with 'commit' wait strategy...")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Try with commit instead of networkidle
            page.goto(url, wait_until='commit', timeout=5000)
            
            # Quick wait
            page.wait_for_timeout(1000)
            
            content = page.evaluate("() => document.body ? document.body.innerText.substring(0, 100) : 'No body'")
            
            print(f"   ✅ Quick load successful")
            print(f"   ✅ First 100 chars: {content}")
            
            browser.close()
            
    except Exception as e:
        print(f"   ❌ Quick load failed: {str(e)[:100]}")

def main():
    print("\n" + "="*80)
    print("TESTING PROBLEMATIC WEBSITES")
    print("="*80)
    
    for ticker, url in problem_sites:
        test_basic_access(ticker, url)
        time.sleep(1)  # Be nice
    
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print("Check results above to see which sites are actually accessible")

if __name__ == "__main__":
    main()