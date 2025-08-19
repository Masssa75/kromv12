#!/usr/bin/env python3
"""
Re-analyze the 4 test tokens using the batch analyzer approach
"""

import os
import sqlite3
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright
from kimi import analyze_with_kimi_k2

def parse_website_with_playwright(url):
    """Parse website with Playwright to get comprehensive content"""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Navigate with timeout
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for main content
            page.wait_for_timeout(3000)
            
            # Get page content
            title = page.title()
            
            # Extract all text content
            text_content = page.evaluate("""
                () => {
                    // Remove scripts and styles
                    const scripts = document.querySelectorAll('script, style');
                    scripts.forEach(el => el.remove());
                    
                    // Get text content
                    return document.body ? document.body.innerText : '';
                }
            """)
            
            # Extract links
            links = page.evaluate("""
                () => {
                    const links = Array.from(document.querySelectorAll('a[href]'));
                    return links.map(link => ({
                        text: link.innerText.trim(),
                        href: link.href
                    })).filter(l => l.text && l.href);
                }
            """)
            
            # Count important elements
            doc_count = len([l for l in links if any(
                keyword in l['text'].lower() or keyword in l['href'].lower() 
                for keyword in ['whitepaper', 'docs', 'documentation', 'litepaper', 'paper', 'pdf']
            )])
            
            linkedin_count = len([l for l in links if 'linkedin.com' in l['href']])
            github_count = len([l for l in links if 'github.com' in l['href'] or 'github' in l['text'].lower()])
            
            # Get full HTML for AI analysis
            html_content = page.content()
            
            browser.close()
            
            return {
                'success': True,
                'content': {
                    'title': title,
                    'text': text_content[:10000],  # Limit text content
                    'html': html_content[:50000],  # Limit HTML for AI
                },
                'links': links[:100],  # Limit links
                'doc_count': doc_count,
                'linkedin_count': linkedin_count,
                'github_count': github_count
            }
            
    except Exception as e:
        print(f"    Parse error: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def main():
    """Re-analyze the 4 test tokens"""
    
    # Connect to database
    conn = sqlite3.connect('website_analysis_new.db')
    cursor = conn.cursor()
    
    # Test tokens
    test_tokens = [
        ('GAI', 'https://www.gaiai.co/'),
        ('MSIA', 'https://messiah.network'),
        ('STRAT', 'https://www.ethstrat.xyz/'),
        ('REX', 'https://www.etherex.finance/')
    ]
    
    print("="*80)
    print("🔄 RE-ANALYZING 4 TEST TOKENS WITH REAL DATA")
    print("="*80)
    
    for i, (ticker, url) in enumerate(test_tokens, 1):
        print(f"\n[{i}/4] {ticker}: {url}")
        print("-"*60)
        
        try:
            # Parse website
            print(f"  📖 Parsing website...")
            parsed = parse_website_with_playwright(url)
            
            if not parsed['success']:
                print(f"  ❌ Failed to parse: {parsed.get('error')}")
                continue
            
            print(f"  ✓ Parsed successfully")
            print(f"    • Documents found: {parsed.get('doc_count', 0)}")
            print(f"    • LinkedIn profiles: {parsed.get('linkedin_count', 0)}")
            print(f"    • GitHub links: {parsed.get('github_count', 0)}")
            
            # Analyze with Kimi K2
            print(f"  🤖 Analyzing with Kimi K2...")
            analysis = analyze_with_kimi_k2(
                url=url,
                ticker=ticker,
                parsed_content=parsed
            )
            
            if analysis and analysis.get('success'):
                result = analysis.get('result', {})
                
                print(f"  ✓ Analysis complete")
                print(f"    • Total Score: {result.get('total_score')}/21")
                print(f"    • Tier: {result.get('tier')}")
                print(f"    • Stage 2: {'Yes' if result.get('proceed_to_stage_2') else 'No'}")
                
                # Update database
                cursor.execute("""
                    UPDATE website_analysis 
                    SET 
                        parsed_content = ?,
                        documents_found = ?,
                        linkedin_profiles = ?,
                        total_score = ?,
                        tier = ?,
                        proceed_to_stage_2 = ?,
                        category_scores = ?,
                        exceptional_signals = ?,
                        missing_elements = ?,
                        quick_assessment = ?,
                        stage_2_links = ?,
                        reasoning = ?,
                        analyzed_at = ?,
                        parse_success = 1
                    WHERE ticker = ?
                """, (
                    json.dumps(parsed),
                    parsed.get('doc_count', 0),
                    parsed.get('linkedin_count', 0),
                    result.get('total_score'),
                    result.get('tier'),
                    result.get('proceed_to_stage_2', False),
                    json.dumps(result.get('category_scores', {})),
                    json.dumps(result.get('exceptional_signals', [])),
                    json.dumps(result.get('missing_elements', [])),
                    result.get('quick_assessment'),
                    json.dumps(result.get('stage_2_links', [])),
                    result.get('reasoning'),
                    datetime.now().isoformat(),
                    ticker
                ))
                conn.commit()
                
                # Show some signals
                signals = result.get('exceptional_signals', [])
                if signals:
                    print(f"    • Positive signals: {len(signals)}")
                    for signal in signals[:2]:
                        print(f"      - {signal}")
                
                missing = result.get('missing_elements', [])
                if missing:
                    print(f"    • Missing elements: {len(missing)}")
                    for element in missing[:2]:
                        print(f"      - {element}")
            else:
                print(f"  ❌ Analysis failed")
        
        except Exception as e:
            print(f"  ❌ Error: {e}")
        
        # Delay between analyses
        if i < 4:
            print(f"\n  ⏳ Waiting 3 seconds...")
            time.sleep(3)
    
    # Final summary
    print("\n" + "="*80)
    print("📊 SUMMARY OF RE-ANALYZED TOKENS")
    print("="*80)
    
    cursor.execute("""
        SELECT ticker, total_score, tier, proceed_to_stage_2
        FROM website_analysis
        WHERE ticker IN ('GAI', 'MSIA', 'STRAT', 'REX')
        ORDER BY total_score DESC
    """)
    
    for row in cursor.fetchall():
        ticker, score, tier, stage2 = row
        status = "✅" if stage2 else "❌"
        print(f"{ticker}: {score}/21 ({tier}) - Stage 2: {status}")
    
    conn.close()
    print("\n✅ Complete! Visit http://localhost:5006 to see updated results")

if __name__ == "__main__":
    main()