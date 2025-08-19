#!/usr/bin/env python3
"""
Debug CREATOR website parsing to see why team wasn't detected
"""
from playwright.sync_api import sync_playwright
import json

def debug_creator():
    url = "https://creatordao.com"
    
    print(f"Debugging {url}")
    print("="*60)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # Show browser
        page = browser.new_page()
        
        # Navigate with longer timeout
        print("1. Navigating to site...")
        page.goto(url, wait_until='domcontentloaded', timeout=30000)
        page.wait_for_timeout(5000)  # Wait longer for JS
        
        # Try different wait strategies
        print("\n2. Checking for team sections...")
        
        # Look for team-related text
        team_keywords = ['team', 'founder', 'ceo', 'cto', 'advisor', 'about us', 'our team', 'leadership']
        for keyword in team_keywords:
            elements = page.locator(f'text=/{keyword}/i').all()
            if elements:
                print(f"   Found '{keyword}': {len(elements)} instances")
        
        # Look for LinkedIn links
        print("\n3. Looking for LinkedIn profiles...")
        linkedin_links = page.locator('a[href*="linkedin.com"]').all()
        print(f"   Found {len(linkedin_links)} LinkedIn links")
        
        for i, link in enumerate(linkedin_links[:5], 1):
            href = link.get_attribute('href')
            text = link.inner_text()
            print(f"   {i}. {text}: {href}")
        
        # Get page content
        print("\n4. Page content length...")
        content = page.evaluate("() => document.body ? document.body.innerText : ''")
        print(f"   Total text content: {len(content)} chars")
        
        # Check if there's dynamic loading
        print("\n5. Checking for dynamic content...")
        
        # Scroll to bottom to trigger lazy loading
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(3000)
        
        content_after_scroll = page.evaluate("() => document.body ? document.body.innerText : ''")
        print(f"   Content after scroll: {len(content_after_scroll)} chars")
        
        if len(content_after_scroll) > len(content):
            print(f"   ✅ Dynamic content loaded: +{len(content_after_scroll) - len(content)} chars")
        
        # Look for team section specifically
        print("\n6. Looking for team section specifically...")
        team_section = page.locator('section:has-text("team"), div:has-text("team")').first
        if team_section:
            try:
                team_text = team_section.inner_text()
                print(f"   Found team section with {len(team_text)} chars")
                print(f"   Preview: {team_text[:200]}...")
            except:
                print("   Team section found but couldn't extract text")
        
        # Check for hidden elements
        print("\n7. Checking for hidden team content...")
        hidden_team = page.evaluate("""
            () => {
                const all = document.querySelectorAll('*');
                let hidden = [];
                all.forEach(el => {
                    const text = el.innerText || '';
                    if (text.toLowerCase().includes('team') || 
                        text.toLowerCase().includes('founder') ||
                        text.toLowerCase().includes('linkedin')) {
                        const style = window.getComputedStyle(el);
                        if (style.display === 'none' || 
                            style.visibility === 'hidden' || 
                            style.opacity === '0') {
                            hidden.push({
                                text: text.substring(0, 100),
                                display: style.display,
                                visibility: style.visibility,
                                opacity: style.opacity
                            });
                        }
                    }
                });
                return hidden;
            }
        """)
        
        if hidden_team:
            print(f"   Found {len(hidden_team)} hidden team-related elements")
            for item in hidden_team[:3]:
                print(f"   - {item}")
        
        # Take screenshot
        page.screenshot(path='creator_website.png')
        print("\n8. Screenshot saved to creator_website.png")
        
        browser.close()

if __name__ == "__main__":
    debug_creator()