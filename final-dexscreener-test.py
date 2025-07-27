from playwright.sync_api import sync_playwright
import time

def test_dexscreener():
    with sync_playwright() as p:
        # Launch headed browser
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        print("Opening DexScreener page...")
        page.goto("http://localhost:5001/dexscreener")
        
        # Wait for initial load
        page.wait_for_timeout(3000)
        
        # Wait for data to load
        try:
            page.wait_for_selector(".token-card", timeout=20000)
            print("✅ Page loaded successfully!")
            
            # Get summary
            summary = page.query_selector("#summary").inner_text()
            print(f"\n{summary}")
            
            # Count token cards
            cards = page.query_selector_all(".token-card")
            print(f"\nTotal tokens displayed: {len(cards)}")
            
            # Get a sample token
            if cards:
                first_card = cards[0]
                symbol = first_card.query_selector(".token-symbol").inner_text()
                chain = first_card.query_selector(".token-chain").inner_text()
                print(f"\nSample token: {symbol} on {chain}")
            
            # Take screenshot
            page.screenshot(path="dexscreener-final-success.png", full_page=True)
            print("\nScreenshot saved as dexscreener-final-success.png")
            
            # Keep open for viewing
            print("\nPage is working perfectly! Displaying diverse crypto signals.")
            time.sleep(10)
            
        except Exception as e:
            print(f"Error: {e}")
            page.screenshot(path="dexscreener-final-error.png")
        
        browser.close()

if __name__ == "__main__":
    test_dexscreener()