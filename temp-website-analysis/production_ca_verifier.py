#!/usr/bin/env python3
"""
Production CA Verifier - Direct website parsing with Playwright
Checks main site, docs, and common contract pages
No AI needed - 100% deterministic
"""

from playwright.sync_api import sync_playwright
import time
import sqlite3
from datetime import datetime
from urllib.parse import urlparse
import re

def generate_urls_to_check(base_url):
    """
    Generate comprehensive list of URLs where contracts might be listed
    """
    parsed = urlparse(base_url)
    domain = parsed.netloc.replace('www.', '')
    project_name = domain.split('.')[0]
    
    # Common documentation and contract page patterns
    urls = [
        base_url,  # Main site
        
        # Documentation subdomains
        f"https://docs.{domain}",
        f"https://doc.{domain}",
        f"https://documentation.{domain}",
        f"https://{project_name}.gitbook.io",
        
        # Contract-specific pages (on main domain)
        f"{base_url.rstrip('/')}/contracts",
        f"{base_url.rstrip('/')}/contract",
        f"{base_url.rstrip('/')}/developers",
        f"{base_url.rstrip('/')}/developer",
        f"{base_url.rstrip('/')}/resources",
        f"{base_url.rstrip('/')}/addresses",
        f"{base_url.rstrip('/')}/docs",
        f"{base_url.rstrip('/')}/documentation",
        f"{base_url.rstrip('/')}/whitepaper",
        f"{base_url.rstrip('/')}/technical",
        
        # Contract pages on docs subdomain
        f"https://docs.{domain}/contracts",
        f"https://docs.{domain}/contract",
        f"https://docs.{domain}/contract-addresses",
        f"https://docs.{domain}/addresses",
        f"https://docs.{domain}/developers",
        f"https://docs.{domain}/resources",
        f"https://docs.{domain}/resources/contracts",
        f"https://docs.{domain}/resources/contract-addresses",
        f"https://docs.{domain}/resources/addresses",
        f"https://docs.{domain}/smart-contracts",
        f"https://docs.{domain}/technical",
        f"https://docs.{domain}/deployment",
        f"https://docs.{domain}/deployments",
    ]
    
    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique.append(url)
    
    return unique

def check_page_for_contract(page, contract_address):
    """
    Check if contract appears on the loaded page
    """
    contract_lower = contract_address.lower()
    contract_no_0x = contract_lower.replace('0x', '')
    
    locations = []
    
    try:
        # Get content
        content = page.content()
        visible_text = page.inner_text('body')
        
        # Check HTML content
        if contract_lower in content.lower():
            locations.append('html')
        elif contract_no_0x in content.lower() and len(contract_no_0x) > 20:
            locations.append('html_no_0x')
        
        # Check visible text
        if contract_lower in visible_text.lower():
            if 'visible_text' not in locations:
                locations.append('visible_text')
        
        # Check links (explorer links)
        links = page.query_selector_all('a[href]')
        for link in links[:100]:  # Limit to first 100 links
            try:
                href = link.get_attribute('href') or ''
                if contract_no_0x in href.lower():
                    if 'explorer_link' not in locations:
                        locations.append('explorer_link')
                    break
            except:
                pass
        
        # Check code blocks (common in docs)
        code_elements = page.query_selector_all('code, pre, .code, .hljs, .language-solidity')
        for elem in code_elements[:50]:  # Limit to first 50 code blocks
            try:
                text = elem.inner_text()
                if contract_lower in text.lower() or contract_no_0x in text.lower():
                    if 'code_block' not in locations:
                        locations.append('code_block')
                    break
            except:
                pass
        
        # Check tables (contracts often in tables)
        table_cells = page.query_selector_all('td, th')
        for cell in table_cells[:100]:  # Limit to first 100 cells
            try:
                text = cell.inner_text()
                if contract_lower in text.lower() or contract_no_0x in text.lower():
                    if 'table' not in locations:
                        locations.append('table')
                    break
            except:
                pass
                
    except Exception as e:
        pass
    
    return len(locations) > 0, locations

def verify_with_playwright(website_url, contract_address, max_urls=10, timeout=15000):
    """
    Verify contract by checking website and documentation pages
    """
    urls_to_check = generate_urls_to_check(website_url)[:max_urls]
    
    result = {
        'found': False,
        'locations': [],
        'checked_urls': [],
        'successful_url': None,
        'error': None
    }
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            
            for url in urls_to_check:
                page = context.new_page()
                
                try:
                    # Try to load the page
                    response = page.goto(url, wait_until='domcontentloaded', timeout=timeout)
                    
                    if response and response.status < 400:
                        # Wait for dynamic content
                        page.wait_for_timeout(2000)
                        
                        # Check for contract
                        found, locations = check_page_for_contract(page, contract_address)
                        
                        result['checked_urls'].append({
                            'url': url,
                            'found': found,
                            'locations': locations
                        })
                        
                        if found:
                            result['found'] = True
                            result['locations'] = locations
                            result['successful_url'] = url
                            page.close()
                            break  # Stop checking once found
                    
                except Exception as e:
                    # Page failed to load, continue to next URL
                    pass
                
                page.close()
            
            browser.close()
            
    except Exception as e:
        result['error'] = str(e)[:200]
    
    return result

def verify_top20_tokens():
    """
    Verify top 20 tokens using direct website parsing
    """
    # Connect to database
    conn = sqlite3.connect('analysis_results.db')
    cursor = conn.cursor()
    
    # Get top 20 tokens
    cursor.execute("""
        SELECT DISTINCT ticker, network, contract_address, website_url 
        FROM website_analysis 
        WHERE website_url IS NOT NULL 
        ORDER BY website_score DESC 
        LIMIT 20
    """)
    
    tokens = cursor.fetchall()
    conn.close()
    
    print("="*80)
    print("PRODUCTION CA VERIFIER - DIRECT WEBSITE PARSING")
    print("="*80)
    print(f"Processing {len(tokens)} tokens...")
    print("Method: Load websites with Playwright, search for contract")
    print("Checking main site + documentation pages\n")
    
    results = []
    legitimate_count = 0
    fake_count = 0
    error_count = 0
    
    for i, (ticker, network, contract, website) in enumerate(tokens, 1):
        print(f"\n[{i}/{len(tokens)}] {ticker} on {network}")
        print(f"  Contract: {contract[:30]}...")
        print(f"  Website: {website}")
        
        # Verify
        result = verify_with_playwright(website, contract)
        
        if result['error']:
            print(f"  ❌ Error: {result['error']}")
            verdict = 'ERROR'
            error_count += 1
        elif result['found']:
            print(f"  ✅ LEGITIMATE - Contract found")
            print(f"  Found at: {result['successful_url']}")
            print(f"  Locations: {', '.join(result['locations'])}")
            verdict = 'LEGITIMATE'
            legitimate_count += 1
        else:
            print(f"  🚫 FAKE - Contract not found")
            print(f"  Checked {len(result['checked_urls'])} URLs")
            verdict = 'FAKE'
            fake_count += 1
        
        # Save to database
        conn = sqlite3.connect('analysis_results.db')
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO ca_verification 
            (ticker, network, contract_address, verification_method, verdict, 
             confidence, website_found_in_results, reasoning, verified_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            ticker, network, contract, 'playwright_production',
            verdict, 100 if verdict != 'ERROR' else 0,
            1 if result['found'] else 0,
            f"Found at {result['successful_url']}" if result['found'] else f"Checked {len(result['checked_urls'])} URLs",
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        
        results.append({
            'ticker': ticker,
            'verdict': verdict,
            'result': result
        })
        
        # Brief pause between tokens
        time.sleep(1)
    
    # Print summary
    print("\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)
    print(f"\n✅ Legitimate: {legitimate_count}")
    print(f"🚫 Fake: {fake_count}")
    print(f"❌ Errors: {error_count}")
    print(f"Total: {len(tokens)}")
    
    success_rate = (legitimate_count + fake_count) / len(tokens) * 100
    print(f"\nSuccess rate: {success_rate:.1f}%")
    
    # List results
    print("\nDetailed Results:")
    print("-"*40)
    for r in results:
        verdict = r['verdict']
        emoji = '✅' if verdict == 'LEGITIMATE' else '🚫' if verdict == 'FAKE' else '❌'
        print(f"{emoji} {r['ticker']:10} - {verdict}")
    
    print(f"\nResults saved to database")
    print("View at: http://localhost:5002/")

if __name__ == "__main__":
    verify_top20_tokens()