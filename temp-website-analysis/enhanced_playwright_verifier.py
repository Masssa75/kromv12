#!/usr/bin/env python3
"""
Enhanced CA Verifier - Checks main site AND documentation sites
Handles GitBook, Notion docs, and other common documentation platforms
"""

from playwright.sync_api import sync_playwright
import time
from urllib.parse import urlparse
import re

def check_documentation_urls(base_url):
    """
    Generate possible documentation URLs based on the main website
    """
    parsed = urlparse(base_url)
    domain = parsed.netloc.replace('www.', '')
    base_domain = domain
    
    # Extract the project name (e.g., "tren" from "tren.finance")
    project_name = domain.split('.')[0]
    
    doc_urls = [
        base_url,  # Main site
        f"https://docs.{domain}",  # docs.project.com
        f"https://{project_name}.gitbook.io",  # project.gitbook.io
        f"https://doc.{domain}",  # doc.project.com
        f"https://documentation.{domain}",  # documentation.project.com
        f"https://{domain}/docs",  # project.com/docs
        f"https://{domain}/documentation",  # project.com/documentation
    ]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in doc_urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    
    return unique_urls

def verify_url_with_playwright(url, contract_address, timeout=15000):
    """
    Check a single URL for the contract address
    """
    contract_lower = contract_address.lower()
    contract_no_0x = contract_lower.replace('0x', '')
    
    result = {
        'url': url,
        'found': False,
        'locations': [],
        'error': None,
        'accessible': False
    }
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = context.new_page()
            
            try:
                # Try to load the page
                response = page.goto(url, wait_until='domcontentloaded', timeout=timeout)
                
                if response and response.status < 400:
                    result['accessible'] = True
                    
                    # Wait for dynamic content
                    page.wait_for_timeout(2000)
                    
                    # Get content
                    content = page.content()
                    visible_text = page.inner_text('body')
                    
                    # Search in HTML
                    if contract_lower in content.lower():
                        result['found'] = True
                        result['locations'].append('html')
                    elif contract_no_0x in content.lower() and len(contract_no_0x) > 20:
                        result['found'] = True
                        result['locations'].append('html_no_prefix')
                    
                    # Search in visible text
                    if contract_lower in visible_text.lower():
                        if 'visible_text' not in result['locations']:
                            result['locations'].append('visible_text')
                        result['found'] = True
                    
                    # Check for explorer links
                    links = page.query_selector_all('a[href*="scan"], a[href*="0x"]')
                    for link in links:
                        href = link.get_attribute('href') or ''
                        if contract_no_0x in href.lower():
                            result['found'] = True
                            if 'explorer_link' not in result['locations']:
                                result['locations'].append('explorer_link')
                            break
                    
                    # Check code blocks (common in docs)
                    code_blocks = page.query_selector_all('code, pre, .code, .hljs')
                    for block in code_blocks:
                        try:
                            block_text = block.inner_text()
                            if contract_lower in block_text.lower() or contract_no_0x in block_text.lower():
                                result['found'] = True
                                if 'code_block' not in result['locations']:
                                    result['locations'].append('code_block')
                                break
                        except:
                            pass
                            
            except Exception as e:
                # Page failed to load
                result['error'] = str(e)[:100]
                
            browser.close()
            
    except Exception as e:
        result['error'] = f"Browser error: {str(e)[:100]}"
    
    return result

def verify_with_docs_check(website_url, contract_address, ticker=None):
    """
    Verify contract by checking main site AND documentation sites
    """
    print(f"\n{'='*60}")
    if ticker:
        print(f"Verifying {ticker}")
    print(f"Contract: {contract_address[:30]}...")
    print(f"Main site: {website_url}")
    print("="*60)
    
    # Generate possible documentation URLs
    doc_urls = check_documentation_urls(website_url)
    
    print(f"\nChecking {len(doc_urls)} possible locations:")
    
    found_on_any = False
    all_results = []
    
    for i, url in enumerate(doc_urls, 1):
        print(f"\n[{i}/{len(doc_urls)}] Checking: {url}")
        
        result = verify_url_with_playwright(url, contract_address)
        all_results.append(result)
        
        if result['error']:
            print(f"  ❌ Error: {result['error']}")
        elif not result['accessible']:
            print(f"  ⚫ Not accessible (404 or doesn't exist)")
        elif result['found']:
            print(f"  ✅ FOUND! Locations: {', '.join(result['locations'])}")
            found_on_any = True
            # If found, we can stop checking
            break
        else:
            print(f"  🔍 Accessible but contract not found")
    
    # Determine verdict
    if found_on_any:
        verdict = 'LEGITIMATE'
        print(f"\n✅ VERDICT: LEGITIMATE - Contract found on project's sites")
    else:
        verdict = 'FAKE'
        print(f"\n🚫 VERDICT: FAKE - Contract not found on any project sites")
    
    return {
        'verdict': verdict,
        'found': found_on_any,
        'results': all_results
    }

def test_problematic_tokens():
    """
    Test tokens that were problematic
    """
    test_cases = [
        {
            'ticker': 'TREN',
            'network': 'base',
            'contract': '0xa77E22bFAeE006D4f9DC2c20D7D337b05125C282',
            'website': 'https://www.tren.finance/',
            'expected': 'LEGITIMATE',
            'note': 'Contract is in GitBook docs'
        },
        {
            'ticker': 'VOCL',
            'network': 'ethereum',
            'contract': '0xfEa2e874C0d06031E65ea7E275070e207c2746Fd',
            'website': 'https://vocalad.ai/',
            'expected': 'LEGITIMATE',
            'note': 'Contract in footer'
        },
        {
            'ticker': 'GRAY',
            'network': 'ethereum',
            'contract': '0xa776A95223C500E81Cb0937B291140fF550ac3E4',
            'website': 'https://www.gradient.trade/',
            'expected': 'LEGITIMATE',
            'note': 'Has explorer link'
        }
    ]
    
    print("="*80)
    print("ENHANCED VERIFIER - CHECKING MAIN SITE + DOCS")
    print("="*80)
    
    for token in test_cases:
        print(f"\n{'='*80}")
        print(f"Testing: {token['ticker']} ({token['note']})")
        print(f"Expected: {token['expected']}")
        
        result = verify_with_docs_check(
            token['website'], 
            token['contract'],
            token['ticker']
        )
        
        if result['verdict'] == token['expected']:
            print(f"✅ TEST PASSED!")
        else:
            print(f"❌ TEST FAILED - Got {result['verdict']}, expected {token['expected']}")
        
        time.sleep(1)

if __name__ == "__main__":
    test_problematic_tokens()