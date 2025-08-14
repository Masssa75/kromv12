#!/usr/bin/env python3
"""
Intelligent Site Analyzer - First discovers site structure, then searches for contracts
Instead of guessing URLs, we analyze the actual site to find documentation links
"""

from playwright.sync_api import sync_playwright
import re
from urllib.parse import urlparse, urljoin
import json

def analyze_site_structure(base_url, contract_address):
    """
    First pass: Analyze the site to understand its structure
    Then: Search for contract in discovered pages
    """
    
    print(f"\n{'='*80}")
    print(f"INTELLIGENT SITE ANALYSIS")
    print(f"Site: {base_url}")
    print(f"Contract: {contract_address[:30]}...")
    print("="*80)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        
        # PHASE 1: Analyze main page
        print("\n📊 PHASE 1: Analyzing main page structure...")
        page = context.new_page()
        
        try:
            page.goto(base_url, wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(2000)
            
            # Extract all links from the page
            links = page.evaluate("""
                () => {
                    const links = [];
                    document.querySelectorAll('a[href]').forEach(a => {
                        const href = a.href;
                        const text = a.innerText || a.textContent || '';
                        const title = a.title || '';
                        links.push({
                            href: href,
                            text: text.trim().substring(0, 50),
                            title: title
                        });
                    });
                    return links;
                }
            """)
            
            print(f"Found {len(links)} links on main page")
            
            # Categorize links
            doc_links = []
            contract_links = []
            social_links = []
            external_links = []
            
            # Keywords that suggest documentation or contracts
            doc_keywords = ['doc', 'docs', 'documentation', 'whitepaper', 'paper', 'guide', 
                           'learn', 'about', 'resources', 'developer', 'technical', 'gitbook', 
                           'notion', 'wiki', 'knowledge', 'faq', 'help']
            
            contract_keywords = ['contract', 'address', 'deployment', 'smart', 'code', 
                                'audit', 'security', 'token', 'explorer', 'scan', 'etherscan',
                                'bscscan', 'polygonscan', 'basescan', 'arbiscan']
            
            social_keywords = ['twitter', 'telegram', 'discord', 'medium', 'github', 
                              'reddit', 'youtube', 'linkedin']
            
            parsed_base = urlparse(base_url)
            base_domain = parsed_base.netloc.replace('www.', '')
            
            for link in links:
                href = link['href']
                text = link['text'].lower()
                
                # Skip empty or anchor links
                if not href or href == '#' or href.startswith('javascript:'):
                    continue
                
                parsed = urlparse(href)
                
                # Check if it's a documentation link
                if any(keyword in href.lower() or keyword in text for keyword in doc_keywords):
                    doc_links.append(link)
                
                # Check if it's a contract-related link
                elif any(keyword in href.lower() or keyword in text for keyword in contract_keywords):
                    contract_links.append(link)
                
                # Check if it's a social link
                elif any(keyword in href.lower() for keyword in social_keywords):
                    social_links.append(link)
                
                # Check if it's an external documentation site
                elif parsed.netloc and base_domain not in parsed.netloc:
                    if any(keyword in parsed.netloc for keyword in ['gitbook', 'notion', 'readthedocs']):
                        doc_links.append(link)
                    else:
                        external_links.append(link)
            
            # Print categorized links
            print(f"\n📚 Documentation/Resource Links: {len(doc_links)}")
            for link in doc_links[:5]:
                print(f"   - {link['text']}: {link['href']}")
            
            print(f"\n🔗 Contract/Explorer Links: {len(contract_links)}")
            for link in contract_links[:5]:
                print(f"   - {link['text']}: {link['href']}")
            
            # PHASE 2: Check main page for contract
            print(f"\n🔍 PHASE 2: Checking main page for contract...")
            
            content = page.content()
            text = page.inner_text('body')
            
            contract_lower = contract_address.lower()
            contract_no_0x = contract_lower.replace('0x', '')
            
            found_on_main = False
            if contract_lower in content.lower() or (contract_no_0x in content.lower() and len(contract_no_0x) > 20):
                print("✅ Contract found on main page!")
                found_on_main = True
                
                # Find where it appears
                if contract_lower in text.lower():
                    print("   Location: Visible text")
                else:
                    print("   Location: HTML (not visible)")
                
                # Check if it's in a link
                for link in contract_links:
                    if contract_no_0x in link['href'].lower():
                        print(f"   Found in explorer link: {link['href'][:80]}")
                        break
            else:
                print("❌ Contract not found on main page")
            
            # PHASE 3: Check documentation pages
            if not found_on_main and doc_links:
                print(f"\n📖 PHASE 3: Checking documentation pages...")
                
                pages_to_check = doc_links[:10]  # Limit to first 10 doc pages
                
                for i, link in enumerate(pages_to_check, 1):
                    print(f"\n[{i}/{len(pages_to_check)}] Checking: {link['text']}")
                    print(f"   URL: {link['href']}")
                    
                    try:
                        # Navigate to the documentation page
                        doc_page = context.new_page()
                        doc_page.goto(link['href'], wait_until='domcontentloaded', timeout=15000)
                        doc_page.wait_for_timeout(2000)
                        
                        doc_content = doc_page.content()
                        
                        if contract_lower in doc_content.lower() or (contract_no_0x in doc_content.lower() and len(contract_no_0x) > 20):
                            print(f"   ✅ CONTRACT FOUND!")
                            
                            # If this is a documentation site, look for more specific pages
                            if 'gitbook' in link['href'] or 'docs' in link['href']:
                                # Try to find links to contract/address pages within docs
                                doc_links_internal = doc_page.evaluate("""
                                    () => {
                                        const links = [];
                                        document.querySelectorAll('a[href]').forEach(a => {
                                            const text = (a.innerText || '').toLowerCase();
                                            const href = a.href;
                                            if (text.includes('contract') || text.includes('address') || 
                                                text.includes('deployment') || href.includes('contract') ||
                                                href.includes('address')) {
                                                links.push({href: href, text: a.innerText});
                                            }
                                        });
                                        return links;
                                    }
                                """)
                                
                                if doc_links_internal:
                                    print(f"   Found {len(doc_links_internal)} contract-related pages in docs:")
                                    for internal_link in doc_links_internal[:3]:
                                        print(f"      - {internal_link['text']}: {internal_link['href'][:60]}")
                            
                            doc_page.close()
                            browser.close()
                            return {
                                'found': True,
                                'location': link['href'],
                                'location_type': 'documentation',
                                'main_has_docs': True
                            }
                        else:
                            print(f"   ❌ Contract not found on this page")
                        
                        doc_page.close()
                        
                    except Exception as e:
                        print(f"   ⚠️ Failed to load: {str(e)[:50]}")
            
            # PHASE 4: If still not found, check contract-related links
            if not found_on_main and contract_links:
                print(f"\n🔍 PHASE 4: Checking contract/explorer links...")
                
                for link in contract_links[:5]:
                    if contract_no_0x in link['href'].lower():
                        print(f"✅ Contract found in explorer link: {link['href']}")
                        browser.close()
                        return {
                            'found': True,
                            'location': 'main_page',
                            'location_type': 'explorer_link',
                            'main_has_docs': len(doc_links) > 0
                        }
            
            browser.close()
            
            # Return analysis results
            return {
                'found': found_on_main,
                'location': 'main_page' if found_on_main else None,
                'location_type': 'main_page' if found_on_main else None,
                'main_has_docs': len(doc_links) > 0,
                'doc_links_found': len(doc_links),
                'contract_links_found': len(contract_links),
                'suggested_urls': [link['href'] for link in doc_links[:5]]
            }
            
        except Exception as e:
            print(f"❌ Error analyzing site: {e}")
            browser.close()
            return {
                'found': False,
                'error': str(e)[:200]
            }

def test_intelligent_analyzer():
    """
    Test the intelligent analyzer on known tokens
    """
    test_cases = [
        {
            'ticker': 'TREN',
            'website': 'https://www.tren.finance/',
            'contract': '0xa77E22bFAeE006D4f9DC2c20D7D337b05125C282',
            'note': 'Has docs link that leads to contract addresses'
        },
        {
            'ticker': 'VOCL',
            'website': 'https://vocalad.ai/',
            'contract': '0xfEa2e874C0d06031E65ea7E275070e207c2746Fd',
            'note': 'Contract in footer/explorer link'
        },
        {
            'ticker': 'GRAY',
            'website': 'https://www.gradient.trade/',
            'contract': '0xa776A95223C500E81Cb0937B291140fF550ac3E4',
            'note': 'Has explorer link'
        }
    ]
    
    print("="*80)
    print("INTELLIGENT SITE ANALYZER TEST")
    print("="*80)
    print("Analyzing site structure before searching for contracts\n")
    
    for test in test_cases:
        print(f"\n{'='*80}")
        print(f"Testing: {test['ticker']}")
        print(f"Note: {test['note']}")
        
        result = analyze_site_structure(test['website'], test['contract'])
        
        print(f"\n📊 ANALYSIS RESULT:")
        print(f"   Found: {result['found']}")
        if result['found']:
            print(f"   Location: {result.get('location', 'unknown')}")
            print(f"   Type: {result.get('location_type', 'unknown')}")
        else:
            print(f"   Documentation links found: {result.get('doc_links_found', 0)}")
            print(f"   Contract links found: {result.get('contract_links_found', 0)}")
            if result.get('suggested_urls'):
                print(f"   Suggested URLs to check:")
                for url in result['suggested_urls']:
                    print(f"      - {url}")

if __name__ == "__main__":
    test_intelligent_analyzer()