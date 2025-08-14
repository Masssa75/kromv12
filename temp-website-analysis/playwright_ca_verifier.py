#!/usr/bin/env python3
"""
CA Verifier using Playwright - Loads JavaScript to get full content
This will work with React/Next.js sites
"""

from playwright.sync_api import sync_playwright
import time
import sqlite3
from datetime import datetime

def verify_with_playwright(website_url, contract_address, headless=True):
    """
    Use Playwright to load the full website with JavaScript
    Then search for the contract address
    """
    result = {
        'found': False,
        'locations': [],
        'error': None,
        'page_title': None
    }
    
    contract_lower = contract_address.lower()
    contract_no_0x = contract_lower.replace('0x', '')
    
    try:
        with sync_playwright() as p:
            # Launch browser
            browser = p.chromium.launch(headless=headless)
            page = browser.new_page()
            
            # Navigate to website
            page.goto(website_url, wait_until='networkidle', timeout=30000)
            
            # Wait a bit for dynamic content
            page.wait_for_timeout(3000)
            
            # Get page title
            result['page_title'] = page.title()
            
            # Get all text content
            text_content = page.content()
            visible_text = page.inner_text('body')
            
            # Search in full HTML
            if contract_lower in text_content.lower():
                result['found'] = True
                result['locations'].append('html_content')
            elif contract_no_0x in text_content.lower() and len(contract_no_0x) > 20:
                result['found'] = True
                result['locations'].append('html_no_prefix')
            
            # Search in visible text
            if contract_lower in visible_text.lower():
                result['found'] = True
                result['locations'].append('visible_text')
            elif contract_no_0x in visible_text.lower() and len(contract_no_0x) > 20:
                result['found'] = True
                result['locations'].append('visible_text_no_prefix')
            
            # Check for copy buttons with contract
            copy_buttons = page.query_selector_all('[class*="copy"], [id*="copy"], button:has-text("Copy")')
            for button in copy_buttons:
                try:
                    button_text = button.inner_text()
                    if contract_lower in button_text.lower() or contract_no_0x in button_text.lower():
                        result['found'] = True
                        result['locations'].append('copy_button')
                        break
                except:
                    pass
            
            # Check footer
            footer = page.query_selector('footer')
            if footer:
                footer_text = footer.inner_text()
                if contract_lower in footer_text.lower() or contract_no_0x in footer_text.lower():
                    result['found'] = True
                    result['locations'].append('footer')
            
            # Check for contract in any clickable element
            links = page.query_selector_all('a[href*="scan"], a[href*="0x"]')
            for link in links:
                href = link.get_attribute('href') or ''
                if contract_no_0x in href.lower():
                    result['found'] = True
                    result['locations'].append('explorer_link')
                    break
            
            browser.close()
            
    except Exception as e:
        result['error'] = str(e)[:200]
    
    return result

def test_known_tokens():
    """
    Test on tokens where we know the answer
    """
    test_cases = [
        {
            'ticker': 'VOCL',
            'network': 'ethereum',
            'contract': '0xfEa2e874C0d06031E65ea7E275070e207c2746Fd',
            'website': 'https://vocalad.ai/',
            'expected': 'LEGITIMATE'
        },
        {
            'ticker': 'GRAY',
            'network': 'ethereum',
            'contract': '0xa776A95223C500E81Cb0937B291140fF550ac3E4',
            'website': 'https://www.gradient.trade/',
            'expected': 'FAKE'
        },
        {
            'ticker': 'TREN',
            'network': 'base',
            'contract': '0xa77E22bFAeE006D4f9DC2c20D7D337b05125C282',
            'website': 'https://www.tren.finance/',
            'expected': 'LEGITIMATE'
        },
        {
            'ticker': 'ETHEREUM',
            'network': 'ethereum',
            'contract': '0x788A4C13A8945B15E2009D4526A3d4aBdB81928D',
            'website': 'https://ultrasound.money/',
            'expected': 'FAKE'
        }
    ]
    
    print("="*80)
    print("PLAYWRIGHT CA VERIFICATION TEST")
    print("="*80)
    print("Loading websites with full JavaScript rendering\n")
    
    correct = 0
    for token in test_cases:
        print(f"\nTesting {token['ticker']} on {token['network']}")
        print(f"  Contract: {token['contract'][:30]}...")
        print(f"  Website: {token['website']}")
        print(f"  Expected: {token['expected']}")
        
        result = verify_with_playwright(token['website'], token['contract'])
        
        if result['error']:
            print(f"  ❌ Error: {result['error']}")
            verdict = 'ERROR'
        elif result['found']:
            print(f"  ✅ FOUND - Contract on website")
            print(f"  Locations: {', '.join(result['locations'])}")
            verdict = 'LEGITIMATE'
        else:
            print(f"  🚫 NOT FOUND - No contract on website")
            verdict = 'FAKE'
        
        if verdict == token['expected']:
            correct += 1
            print(f"  ✅ CORRECT!")
        else:
            print(f"  ❌ WRONG! Got {verdict}, expected {token['expected']}")
    
    accuracy = correct / len(test_cases) * 100
    print(f"\n{'='*80}")
    print(f"ACCURACY: {correct}/{len(test_cases)} = {accuracy:.0f}%")
    print("="*80)

def verify_top20_with_playwright():
    """
    Verify top 20 tokens using Playwright
    """
    conn = sqlite3.connect('analysis_results.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT ticker, network, contract_address, website_url 
        FROM website_analysis 
        WHERE website_url IS NOT NULL 
        ORDER BY website_score DESC 
        LIMIT 20
    """)
    
    tokens = cursor.fetchall()
    conn.close()
    
    print("\n" + "="*80)
    print("VERIFYING TOP 20 WITH PLAYWRIGHT")
    print("="*80)
    
    results = []
    legitimate = 0
    fake = 0
    errors = 0
    
    for i, (ticker, network, contract, website) in enumerate(tokens, 1):
        print(f"\n[{i}/20] {ticker} on {network}")
        print(f"  Website: {website}")
        
        result = verify_with_playwright(website, contract)
        
        if result['error']:
            print(f"  ❌ Error: {result['error']}")
            verdict = 'ERROR'
            errors += 1
        elif result['found']:
            print(f"  ✅ LEGITIMATE - Contract found")
            if result['locations']:
                print(f"  Locations: {', '.join(result['locations'])}")
            verdict = 'LEGITIMATE'
            legitimate += 1
        else:
            print(f"  🚫 FAKE - Contract not found")
            verdict = 'FAKE'
            fake += 1
        
        results.append({
            'ticker': ticker,
            'verdict': verdict,
            'locations': result.get('locations', [])
        })
        
        # Save to database
        conn = sqlite3.connect('analysis_results.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO ca_verification 
            (ticker, network, contract_address, verification_method, verdict, 
             confidence, website_found_in_results, reasoning, verified_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticker, network, contract, 'playwright',
            verdict, 100 if verdict != 'ERROR' else 0,
            1 if result['found'] else 0,
            f"Locations: {', '.join(result['locations'])}" if result['locations'] else 'Not found',
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"✅ Legitimate: {legitimate}")
    print(f"🚫 Fake: {fake}")
    print(f"❌ Errors: {errors}")
    print(f"Success rate: {(legitimate + fake)/20*100:.0f}%")
    print("="*80)

if __name__ == "__main__":
    # First test known tokens
    print("Testing known tokens first...\n")
    test_known_tokens()
    
    # Then verify top 20
    print("\n" + "="*80)
    print("Now testing TOP 20 TOKENS...")
    print("="*80)
    time.sleep(2)
    verify_top20_with_playwright()