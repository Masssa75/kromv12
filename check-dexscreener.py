import asyncio
from playwright.async_api import async_playwright
import os

async def check_dexscreener():
    async with async_playwright() as p:
        # Launch browser in headed mode (visible)
        browser = await p.chromium.launch(headless=False)
        page = await browser.new_page()
        
        try:
            print("Opening http://localhost:5001/dexscreener...")
            
            # Navigate to the page
            await page.goto("http://localhost:5001/dexscreener", wait_until="networkidle")
            
            # Wait a bit more to ensure everything is loaded
            await page.wait_for_timeout(2000)
            
            # Take a screenshot
            screenshot_path = "/Users/marcschwyn/Desktop/projects/KROMV12/dexscreener-screenshot.png"
            await page.screenshot(path=screenshot_path)
            print(f"Screenshot saved to: {screenshot_path}")
            
            # Get page title and some basic info
            title = await page.title()
            print(f"Page title: {title}")
            
            # Try to get some visible text content
            try:
                # Look for any headings
                headings = await page.query_selector_all("h1, h2, h3")
                if headings:
                    print("\nVisible headings:")
                    for h in headings[:5]:  # First 5 headings
                        text = await h.inner_text()
                        print(f"  - {text}")
                
                # Look for any error messages
                error_elements = await page.query_selector_all(".error, .alert, [class*='error']")
                if error_elements:
                    print("\nPossible error messages:")
                    for e in error_elements[:3]:
                        text = await e.inner_text()
                        print(f"  - {text}")
                
                # Check if there's a main content area
                main_content = await page.query_selector("main, #root, .container, body")
                if main_content:
                    content_text = await main_content.inner_text()
                    # Print first 500 characters of content
                    print(f"\nFirst 500 chars of visible content:")
                    print(content_text[:500])
                    
            except Exception as e:
                print(f"Error getting page content: {e}")
            
            # Keep browser open for 5 seconds so you can see it
            print("\nKeeping browser open for 5 seconds...")
            await page.wait_for_timeout(5000)
            
        except Exception as e:
            print(f"Error: {e}")
            # Try to see if it's a connection error
            if "net::ERR_CONNECTION_REFUSED" in str(e):
                print("Connection refused - the server might not be running on port 5001")
            
        finally:
            await browser.close()
            print("Browser closed.")

# Run the async function
if __name__ == "__main__":
    asyncio.run(check_dexscreener())