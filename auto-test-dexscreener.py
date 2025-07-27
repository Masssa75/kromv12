#!/usr/bin/env python3
"""
Automated Playwright test for DexScreener that takes screenshots,
analyzes results, and helps fix issues
"""
import asyncio
from playwright.async_api import async_playwright
import os
import json
from datetime import datetime

async def test_and_fix_dexscreener():
    """Test DexScreener page, take screenshots, and analyze issues"""
    
    print("🎭 Starting automated DexScreener testing")
    print("=" * 60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Show browser for debugging
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2  # High quality screenshots
        )
        page = await context.new_page()
        
        # Enable console logging
        page.on("console", lambda msg: print(f"Browser console: {msg.text}"))
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "tests": []
        }
        
        try:
            # Test 1: Load the page
            print("\n📍 Test 1: Loading DexScreener page...")
            await page.goto('http://localhost:5001/dexscreener', wait_until='networkidle')
            await page.wait_for_timeout(2000)
            
            # Screenshot 1: Initial state
            await page.screenshot(path='test-1-initial.png', full_page=True)
            print("✅ Screenshot saved: test-1-initial.png")
            
            # Test 2: Check page elements
            print("\n📍 Test 2: Checking page elements...")
            
            # Check title
            title = await page.text_content('h1')
            print(f"   Page title: {title}")
            
            # Check summary
            summary = await page.text_content('#summary')
            print(f"   Summary: {summary.strip()}")
            
            # Count signal categories
            categories = await page.query_selector_all('.signal-category')
            print(f"   Signal categories found: {len(categories)}")
            
            # Test 3: Click refresh and wait
            print("\n📍 Test 3: Refreshing signals...")
            
            # Intercept API call to see response
            api_response = None
            async def handle_response(response):
                nonlocal api_response
                if '/api/dexscreener/signals' in response.url:
                    api_response = await response.json()
                    print(f"   API Response captured!")
            
            page.on("response", handle_response)
            
            # Click refresh
            await page.click('button:has-text("Refresh Signals")')
            print("   Clicked refresh button")
            
            # Wait for API response
            await page.wait_for_timeout(5000)
            
            # Screenshot 2: After refresh
            await page.screenshot(path='test-2-after-refresh.png', full_page=True)
            print("✅ Screenshot saved: test-2-after-refresh.png")
            
            # Test 4: Analyze each category
            print("\n📍 Test 4: Analyzing signal categories...")
            
            category_data = []
            for i, category in enumerate(await page.query_selector_all('.signal-category')):
                h2 = await category.query_selector('h2')
                title = await h2.text_content() if h2 else "Unknown"
                
                # Count tokens in this category
                tokens = await category.query_selector_all('.token-card')
                
                # Take category screenshot
                await category.screenshot(path=f'test-3-category-{i}.png')
                
                category_info = {
                    "title": title.strip(),
                    "token_count": len(tokens),
                    "tokens": []
                }
                
                # Get first 2 tokens details
                for j, token in enumerate(tokens[:2]):
                    symbol_elem = await token.query_selector('.token-symbol')
                    symbol = await symbol_elem.text_content() if symbol_elem else "N/A"
                    
                    chain_elem = await token.query_selector('.token-chain')
                    chain = await chain_elem.text_content() if chain_elem else "N/A"
                    
                    category_info["tokens"].append({
                        "symbol": symbol.strip(),
                        "chain": chain.strip()
                    })
                
                category_data.append(category_info)
                print(f"\n   {title}: {len(tokens)} tokens")
                if len(tokens) > 0:
                    print(f"     First token: {category_info['tokens'][0]['symbol']} on {category_info['tokens'][0]['chain']}")
            
            # Test 5: Check for empty categories
            print("\n📍 Test 5: Checking for issues...")
            
            empty_categories = [cat for cat in category_data if cat["token_count"] == 0]
            if empty_categories:
                print(f"   ⚠️  Empty categories found: {[cat['title'] for cat in empty_categories]}")
            else:
                print("   ✅ All categories have tokens!")
            
            # Save API response if captured
            if api_response:
                with open('test-api-response.json', 'w') as f:
                    json.dump(api_response, f, indent=2)
                print("\n📍 API Response Analysis:")
                if 'summary' in api_response:
                    summary = api_response['summary']
                    print(f"   New Launches: {summary.get('new_launches', 0)}")
                    print(f"   Volume Spikes: {summary.get('volume_spikes', 0)}")
                    print(f"   Boosted Tokens: {summary.get('boosted_tokens', 0)}")
            
            # Test 6: Open browser console
            print("\n📍 Test 6: Checking for JavaScript errors...")
            
            # Execute JavaScript to check for errors
            js_errors = await page.evaluate('''() => {
                const errors = [];
                // Check if any error elements exist
                const errorElements = document.querySelectorAll('.loading');
                errorElements.forEach(el => {
                    if (el.textContent.includes('Error')) {
                        errors.push(el.textContent);
                    }
                });
                return errors;
            }''')
            
            if js_errors:
                print(f"   ❌ JavaScript errors found: {js_errors}")
            else:
                print("   ✅ No JavaScript errors")
            
            # Final summary
            print("\n" + "=" * 60)
            print("📊 TEST SUMMARY:")
            print(f"- Page loaded: ✅")
            print(f"- Categories found: {len(category_data)}")
            for cat in category_data:
                status = "✅" if cat["token_count"] > 0 else "❌"
                print(f"- {cat['title']}: {cat['token_count']} tokens {status}")
            print(f"\nScreenshots saved:")
            print("- test-1-initial.png")
            print("- test-2-after-refresh.png")
            print(f"- test-3-category-0.png through test-3-category-{len(category_data)-1}.png")
            
            # Save results
            results["tests"] = category_data
            results["api_response_saved"] = api_response is not None
            
            with open('test-results.json', 'w') as f:
                json.dump(results, f, indent=2)
            
        except Exception as e:
            print(f"\n❌ Error during testing: {e}")
            await page.screenshot(path='test-error.png', full_page=True)
            print("Error screenshot saved: test-error.png")
        
        finally:
            # Keep browser open for 5 seconds to see final state
            print("\n⏳ Keeping browser open for inspection...")
            await page.wait_for_timeout(5000)
            await browser.close()
    
    print("\n✅ Testing complete! Check the screenshots to see what's displayed.")
    return results

# Main execution
if __name__ == "__main__":
    # Check if Playwright is installed
    try:
        import playwright
        print("✅ Playwright is installed")
        
        # Check if server is running
        import requests
        try:
            response = requests.get('http://localhost:5001/api/health', timeout=2)
            if response.status_code == 200:
                print("✅ Server is running")
                
                # Run the test
                results = asyncio.run(test_and_fix_dexscreener())
                
            else:
                print("❌ Server returned status:", response.status_code)
        except:
            print("❌ Server is not running!")
            print("Please start it with: python3 all-in-one-server.py")
            
    except ImportError:
        print("❌ Playwright is NOT installed!")
        print("Install with:")
        print("  pip3 install playwright")
        print("  playwright install chromium")