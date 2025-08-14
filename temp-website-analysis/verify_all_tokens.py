#!/usr/bin/env python3
"""
Production CA Verifier - Verify ALL tokens in database
No AI needed - Pure website parsing with intelligent link discovery
"""

from playwright.sync_api import sync_playwright
import sqlite3
import time
from datetime import datetime
from urllib.parse import urlparse, urljoin
import re
import json

class IntelligentCAVerifier:
    def __init__(self, headless=True):
        self.headless = headless
        self.stats = {
            'total': 0,
            'verified': 0,
            'legitimate': 0,
            'fake': 0,
            'errors': 0,
            'no_website': 0
        }
    
    def analyze_and_verify(self, website_url, contract_address, ticker=None):
        """
        Intelligently analyze site structure and verify contract
        """
        if not website_url or website_url == 'None':
            return {
                'found': False,
                'error': 'No website URL',
                'verdict': 'NO_WEBSITE'
            }
        
        # Clean up URL
        if not website_url.startswith('http'):
            website_url = 'https://' + website_url
        
        contract_lower = contract_address.lower()
        contract_no_0x = contract_lower.replace('0x', '')
        
        result = {
            'found': False,
            'location': None,
            'location_type': None,
            'checked_urls': [],
            'error': None
        }
        
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=self.headless)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                
                # STEP 1: Load and analyze main page
                page = context.new_page()
                
                try:
                    response = page.goto(website_url, wait_until='domcontentloaded', timeout=20000)
                    
                    if not response or response.status >= 400:
                        result['error'] = f"Failed to load: HTTP {response.status if response else 'timeout'}"
                        browser.close()
                        return result
                    
                    page.wait_for_timeout(2000)
                    
                    # Check main page for contract
                    content = page.content()
                    visible_text = page.inner_text('body')
                    
                    # Quick check for contract on main page
                    if contract_lower in content.lower() or (contract_no_0x in content.lower() and len(contract_no_0x) > 20):
                        result['found'] = True
                        result['location'] = website_url
                        result['location_type'] = 'main_page'
                        
                        # Check if it's visible or just in HTML
                        if contract_lower in visible_text.lower():
                            result['location_type'] = 'main_page_visible'
                        
                        browser.close()
                        return result
                    
                    # STEP 2: Extract and categorize all links
                    links = page.evaluate("""
                        () => {
                            const links = [];
                            document.querySelectorAll('a[href]').forEach(a => {
                                const href = a.href;
                                const text = (a.innerText || a.textContent || '').trim();
                                if (href && href !== '#' && !href.startsWith('javascript:')) {
                                    links.push({
                                        href: href,
                                        text: text.substring(0, 100)
                                    });
                                }
                            });
                            return links;
                        }
                    """)
                    
                    # Keywords for finding documentation and contract pages
                    doc_keywords = ['doc', 'docs', 'documentation', 'whitepaper', 'guide', 
                                   'resources', 'developer', 'technical', 'gitbook', 'notion']
                    
                    contract_keywords = ['contract', 'address', 'deployment', 'token', 
                                        'explorer', 'scan', 'etherscan', 'bscscan', 'basescan']
                    
                    # Categorize links
                    priority_links = []
                    
                    for link in links:
                        href = link['href'].lower()
                        text = link['text'].lower()
                        
                        # Score each link
                        score = 0
                        
                        # High priority for documentation
                        for keyword in doc_keywords:
                            if keyword in href or keyword in text:
                                score += 2
                        
                        # Very high priority for contract-related
                        for keyword in contract_keywords:
                            if keyword in href or keyword in text:
                                score += 3
                        
                        # Check if link already contains the contract
                        if contract_no_0x in href:
                            result['found'] = True
                            result['location'] = link['href']
                            result['location_type'] = 'explorer_link'
                            browser.close()
                            return result
                        
                        if score > 0:
                            priority_links.append({
                                'href': link['href'],
                                'text': link['text'],
                                'score': score
                            })
                    
                    # Sort by score
                    priority_links.sort(key=lambda x: x['score'], reverse=True)
                    
                    # STEP 3: Check high-priority pages
                    pages_checked = 0
                    max_pages = 10
                    
                    for link in priority_links[:max_pages]:
                        if pages_checked >= max_pages:
                            break
                        
                        try:
                            # Skip if already checked or same as main
                            if link['href'] in result['checked_urls'] or link['href'] == website_url:
                                continue
                            
                            result['checked_urls'].append(link['href'])
                            
                            # Open new page
                            sub_page = context.new_page()
                            sub_response = sub_page.goto(link['href'], wait_until='domcontentloaded', timeout=15000)
                            
                            if sub_response and sub_response.status < 400:
                                sub_page.wait_for_timeout(1500)
                                
                                sub_content = sub_page.content()
                                
                                # Check for contract
                                if contract_lower in sub_content.lower() or (contract_no_0x in sub_content.lower() and len(contract_no_0x) > 20):
                                    result['found'] = True
                                    result['location'] = link['href']
                                    result['location_type'] = 'documentation'
                                    
                                    # If this is a docs site, try to find more specific contract pages
                                    if any(keyword in link['href'].lower() for keyword in ['doc', 'gitbook']):
                                        # Look for contract-specific pages within docs
                                        contract_links = sub_page.evaluate("""
                                            () => {
                                                const links = [];
                                                document.querySelectorAll('a[href]').forEach(a => {
                                                    const text = (a.innerText || '').toLowerCase();
                                                    const href = a.href;
                                                    if (text.includes('contract') || text.includes('address') || 
                                                        text.includes('deployment') || href.includes('contract') ||
                                                        href.includes('address')) {
                                                        links.push(href);
                                                    }
                                                });
                                                return links;
                                            }
                                        """)
                                        
                                        # Check these contract-specific pages
                                        for contract_link in contract_links[:3]:
                                            try:
                                                contract_page = context.new_page()
                                                contract_response = contract_page.goto(contract_link, timeout=10000)
                                                
                                                if contract_response and contract_response.status < 400:
                                                    contract_page.wait_for_timeout(1000)
                                                    contract_content = contract_page.content()
                                                    
                                                    if contract_lower in contract_content.lower() or (contract_no_0x in contract_content.lower() and len(contract_no_0x) > 20):
                                                        result['location'] = contract_link
                                                        result['location_type'] = 'documentation_contracts'
                                                        contract_page.close()
                                                        break
                                                
                                                contract_page.close()
                                            except:
                                                pass
                                    
                                    sub_page.close()
                                    browser.close()
                                    return result
                            
                            sub_page.close()
                            pages_checked += 1
                            
                        except Exception as e:
                            # Page failed to load, continue
                            pass
                    
                except Exception as e:
                    result['error'] = f"Main page error: {str(e)[:100]}"
                
                browser.close()
                
        except Exception as e:
            result['error'] = f"Browser error: {str(e)[:100]}"
        
        return result
    
    def verify_all_tokens(self):
        """
        Verify all tokens in the database
        """
        # Connect to database
        conn = sqlite3.connect('analysis_results.db')
        cursor = conn.cursor()
        
        # Get all unique tokens with websites
        cursor.execute("""
            SELECT DISTINCT ticker, network, contract_address, website_url
            FROM website_analysis
            ORDER BY website_score DESC
        """)
        
        tokens = cursor.fetchall()
        total = len(tokens)
        
        print("="*80)
        print("CA VERIFICATION - ALL TOKENS")
        print("="*80)
        print(f"Found {total} tokens to verify")
        print("Method: Intelligent website parsing (no AI)")
        print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Create results table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ca_verification_final (
                ticker TEXT,
                network TEXT,
                contract_address TEXT,
                website_url TEXT,
                verdict TEXT,
                found_location TEXT,
                location_type TEXT,
                urls_checked INTEGER,
                error TEXT,
                verified_at TIMESTAMP,
                PRIMARY KEY (ticker, network, contract_address)
            )
        """)
        conn.commit()
        
        # Process each token
        for i, (ticker, network, contract, website) in enumerate(tokens, 1):
            print(f"\n[{i}/{total}] {ticker} on {network}")
            print(f"  Website: {website if website else 'No website'}")
            
            if not website or website == 'None':
                self.stats['no_website'] += 1
                print(f"  ⚫ No website to check")
                
                # Save to database
                cursor.execute("""
                    INSERT OR REPLACE INTO ca_verification_final
                    (ticker, network, contract_address, website_url, verdict, 
                     found_location, location_type, urls_checked, error, verified_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    ticker, network, contract, website, 'NO_WEBSITE',
                    None, None, 0, 'No website URL', datetime.now().isoformat()
                ))
                conn.commit()
                continue
            
            # Verify the token
            result = self.analyze_and_verify(website, contract, ticker)
            
            # Determine verdict
            if result.get('error'):
                if 'Failed to load' in result['error'] or 'timeout' in result['error']:
                    verdict = 'WEBSITE_DOWN'
                    emoji = '⚠️'
                else:
                    verdict = 'ERROR'
                    emoji = '❌'
                self.stats['errors'] += 1
                print(f"  {emoji} {verdict}: {result['error'][:50]}")
            elif result['found']:
                verdict = 'LEGITIMATE'
                emoji = '✅'
                self.stats['legitimate'] += 1
                print(f"  {emoji} LEGITIMATE - Contract found")
                print(f"     Location: {result['location'][:60]}...")
                print(f"     Type: {result['location_type']}")
            else:
                verdict = 'FAKE'
                emoji = '🚫'
                self.stats['fake'] += 1
                print(f"  {emoji} FAKE - Contract not found")
                print(f"     Checked {len(result.get('checked_urls', []))} pages")
            
            self.stats['verified'] += 1
            
            # Save to database
            cursor.execute("""
                INSERT OR REPLACE INTO ca_verification_final
                (ticker, network, contract_address, website_url, verdict, 
                 found_location, location_type, urls_checked, error, verified_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ticker, network, contract, website, verdict,
                result.get('location'), result.get('location_type'),
                len(result.get('checked_urls', [])),
                result.get('error'), datetime.now().isoformat()
            ))
            conn.commit()
            
            # Progress update every 10 tokens
            if i % 10 == 0:
                print(f"\n--- Progress: {i}/{total} ({i/total*100:.1f}%) ---")
                print(f"Legitimate: {self.stats['legitimate']}, Fake: {self.stats['fake']}, Errors: {self.stats['errors']}")
            
            # Small delay to be nice to servers
            time.sleep(0.5)
        
        # Final summary
        print("\n" + "="*80)
        print("VERIFICATION COMPLETE")
        print("="*80)
        print(f"Total tokens: {total}")
        print(f"✅ Legitimate: {self.stats['legitimate']} ({self.stats['legitimate']/total*100:.1f}%)")
        print(f"🚫 Fake: {self.stats['fake']} ({self.stats['fake']/total*100:.1f}%)")
        print(f"⚫ No website: {self.stats['no_website']} ({self.stats['no_website']/total*100:.1f}%)")
        print(f"❌ Errors: {self.stats['errors']} ({self.stats['errors']/total*100:.1f}%)")
        print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Show some interesting findings
        print("\n" + "="*80)
        print("SAMPLE RESULTS")
        print("="*80)
        
        cursor.execute("""
            SELECT ticker, verdict, location_type, found_location
            FROM ca_verification_final
            WHERE verdict = 'LEGITIMATE'
            ORDER BY RANDOM()
            LIMIT 5
        """)
        
        print("\n✅ Sample LEGITIMATE tokens:")
        for row in cursor.fetchall():
            print(f"  {row[0]}: {row[2]} - {row[3][:60] if row[3] else 'N/A'}...")
        
        cursor.execute("""
            SELECT ticker, verdict, urls_checked
            FROM ca_verification_final
            WHERE verdict = 'FAKE'
            ORDER BY urls_checked DESC
            LIMIT 5
        """)
        
        print("\n🚫 Sample FAKE tokens (checked most pages):")
        for row in cursor.fetchall():
            print(f"  {row[0]}: Checked {row[2]} pages, still not found")
        
        conn.close()
        
        print(f"\nResults saved to: ca_verification_final table")
        print("View with: sqlite3 analysis_results.db 'SELECT * FROM ca_verification_final'")

if __name__ == "__main__":
    verifier = IntelligentCAVerifier(headless=True)
    verifier.verify_all_tokens()