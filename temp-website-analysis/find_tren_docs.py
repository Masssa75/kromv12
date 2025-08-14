#!/usr/bin/env python3
"""
Find where TREN's documentation actually is
"""

from playwright.sync_api import sync_playwright
import re

def find_docs_link(website_url):
    """
    Visit the main website and look for documentation links
    """
    print(f"Searching for documentation links on {website_url}")
    print("="*60)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto(website_url, wait_until='networkidle', timeout=30000)
        page.wait_for_timeout(2000)
        
        # Look for documentation links
        doc_patterns = [
            'docs', 'documentation', 'gitbook', 'notion', 
            'whitepaper', 'developer', 'technical', 'contracts'
        ]
        
        # Get all links
        links = page.query_selector_all('a')
        found_links = []
        
        for link in links:
            try:
                href = link.get_attribute('href')
                text = link.inner_text().lower()
                
                if href:
                    # Check if link text or href contains documentation keywords
                    for pattern in doc_patterns:
                        if pattern in text or pattern in href.lower():
                            found_links.append({
                                'text': link.inner_text(),
                                'href': href
                            })
                            break
            except:
                pass
        
        # Also check the page content for GitBook or other doc platform references
        content = page.content()
        
        # Look for GitBook embeds or links
        gitbook_matches = re.findall(r'https://[^"\'<>\s]*gitbook[^"\'<>\s]*', content, re.IGNORECASE)
        for match in gitbook_matches:
            found_links.append({
                'text': 'GitBook embed/link found',
                'href': match
            })
        
        # Look for Notion links
        notion_matches = re.findall(r'https://[^"\'<>\s]*notion[^"\'<>\s]*', content, re.IGNORECASE)
        for match in notion_matches:
            found_links.append({
                'text': 'Notion link found',
                'href': match
            })
        
        browser.close()
        
        # Remove duplicates
        unique_links = []
        seen_hrefs = set()
        for link in found_links:
            if link['href'] not in seen_hrefs:
                seen_hrefs.add(link['href'])
                unique_links.append(link)
        
        return unique_links

# Test on TREN
print("FINDING TREN DOCUMENTATION")
print("="*80)
print()

docs_links = find_docs_link('https://www.tren.finance/')

if docs_links:
    print(f"\nFound {len(docs_links)} documentation-related links:")
    for i, link in enumerate(docs_links, 1):
        print(f"\n{i}. {link['text']}")
        print(f"   URL: {link['href']}")
else:
    print("\nNo documentation links found")

# Now check if any of these contain the contract
print("\n" + "="*80)
print("CHECKING FOUND LINKS FOR CONTRACT")
print("="*80)

contract = '0xa77E22bFAeE006D4f9DC2c20D7D337b05125C282'

if docs_links:
    from playwright.sync_api import sync_playwright
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        
        for link in docs_links:
            url = link['href']
            
            # Skip if it's not a full URL
            if not url.startswith('http'):
                continue
                
            print(f"\nChecking: {url}")
            
            try:
                page = browser.new_page()
                page.goto(url, wait_until='domcontentloaded', timeout=15000)
                page.wait_for_timeout(2000)
                
                content = page.content()
                
                if contract.lower() in content.lower():
                    print(f"  ✅ CONTRACT FOUND!")
                    
                    # Try to find context
                    pos = content.lower().find(contract.lower())
                    snippet = content[max(0, pos-100):min(len(content), pos+200)]
                    # Clean up the snippet
                    snippet = re.sub(r'<[^>]+>', '', snippet)
                    print(f"  Context: ...{snippet}...")
                else:
                    print(f"  ❌ Contract not found")
                    
                page.close()
            except Exception as e:
                print(f"  ❌ Error: {str(e)[:100]}")
        
        browser.close()