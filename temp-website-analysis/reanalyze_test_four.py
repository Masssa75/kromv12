#!/usr/bin/env python3
"""
Re-analyze just the 4 test tokens with Kimi K2
This is a modified version of batch_analyze_supabase_utility.py
"""

import sqlite3
import json
import time
import os
from datetime import datetime
from playwright.sync_api import sync_playwright

# OpenRouter API configuration for Kimi K2
OPEN_ROUTER_API_KEY = "OPENROUTER_API_KEY_REMOVED"
OPEN_ROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"

def parse_website_with_playwright(url):
    """Parse website using Playwright"""
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            page.goto(url, wait_until='networkidle', timeout=30000)
            page.wait_for_timeout(3000)
            
            title = page.title()
            text_content = page.evaluate("""
                () => {
                    const scripts = document.querySelectorAll('script, style');
                    scripts.forEach(el => el.remove());
                    return document.body ? document.body.innerText : '';
                }
            """)
            
            links = page.evaluate("""
                () => {
                    const links = Array.from(document.querySelectorAll('a[href]'));
                    return links.map(link => ({
                        text: link.innerText.trim(),
                        href: link.href
                    })).filter(l => l.text && l.href);
                }
            """)
            
            html_content = page.content()
            browser.close()
            
            return {
                'success': True,
                'content': {
                    'title': title,
                    'text': text_content[:10000],
                    'html': html_content[:50000],
                },
                'links': links[:100]
            }
    except Exception as e:
        return {'success': False, 'error': str(e)}

def analyze_with_kimi_k2(url, ticker, parsed_content):
    """Analyze with Kimi K2 using Stage 1 assessment prompt"""
    import requests
    
    prompt = f"""
    Analyze this crypto project website for investment potential using our Stage 1 rapid assessment framework.

    URL: {url}
    Ticker: {ticker}
    
    Website Content:
    {parsed_content.get('content', {}).get('text', '')[:8000]}
    
    Links Found:
    {json.dumps(parsed_content.get('links', [])[:50], indent=2)}

    STAGE 1 ASSESSMENT FRAMEWORK (1-3 scoring, 7 categories):

    Score each category 1-3:
    - 1 = Poor/Missing
    - 2 = Adequate/Standard  
    - 3 = Exceptional/Outstanding

    Categories to evaluate:
    1. Technical Infrastructure (GitHub, code, tech stack, development activity)
    2. Business & Utility (real use case, problem solving, market fit, tokenomics)
    3. Documentation (whitepaper, docs, technical depth, roadmap clarity)
    4. Community & Social (Twitter, Discord, Telegram activity, engagement metrics)
    5. Security & Trust (audits, KYC, locked liquidity, safety measures)
    6. Team Transparency (real names, LinkedIn profiles, track record, advisors)
    7. Website Presentation (professional design, clear messaging, working features)

    IMPORTANT SCORING NOTES:
    - Finding major backers (a16z, Binance, etc.) = instant 3 for Business & Utility
    - Full team with LinkedIn profiles = instant 3 for Team Transparency
    - Multiple security audits = instant 3 for Security & Trust
    - No team information at all = instant 1 for Team Transparency
    - Generic template website = instant 1 for Website Presentation

    Return a JSON object with:
    {{
        "category_scores": {{
            "technical_infrastructure": 1-3,
            "business_utility": 1-3,
            "documentation_quality": 1-3,
            "community_social": 1-3,
            "security_trust": 1-3,
            "team_transparency": 1-3,
            "website_presentation": 1-3
        }},
        "total_score": sum of all scores,
        "tier": "HIGH" (15-21), "MEDIUM" (10-14), or "LOW" (7-9),
        "proceed_to_stage_2": true if total >= 10,
        "exceptional_signals": ["list of strong positive indicators found"],
        "missing_elements": ["list of critical missing items"],
        "quick_assessment": "One paragraph assessment of the project",
        "stage_2_links": ["priority links to analyze in Stage 2 if proceeding"],
        "reasoning": "Brief explanation of the scoring"
    }}
    """
    
    try:
        response = requests.post(
            OPEN_ROUTER_API_URL,
            headers={
                "Authorization": f"Bearer {OPEN_ROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://krom.app",
                "X-Title": "KROM Website Analyzer"
            },
            json={
                "model": "moonshotai/kimi-k2",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            return json.loads(content)
        else:
            print(f"API error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return None
    except Exception as e:
        print(f"Analysis error: {e}")
        return None

def main():
    """Re-analyze the 4 test tokens"""
    
    # Connect to database
    conn = sqlite3.connect('website_analysis_new.db')
    cursor = conn.cursor()
    
    # Get the 4 test tokens
    cursor.execute("""
        SELECT ticker, url 
        FROM website_analysis 
        WHERE ticker IN ('GAI', 'MSIA', 'STRAT', 'REX')
    """)
    
    tokens = cursor.fetchall()
    
    print("="*80)
    print("🔄 RE-ANALYZING 4 TEST TOKENS WITH KIMI K2")
    print("="*80)
    
    for i, (ticker, url) in enumerate(tokens, 1):
        print(f"\n[{i}/4] {ticker}: {url}")
        print("-"*60)
        
        # Parse website
        print("  📖 Parsing website...")
        parsed = parse_website_with_playwright(url)
        
        if not parsed['success']:
            print(f"  ❌ Parse failed: {parsed.get('error')}")
            continue
        
        print("  ✓ Parsed successfully")
        
        # Analyze with Kimi K2
        print("  🤖 Analyzing with Kimi K2...")
        result = analyze_with_kimi_k2(url, ticker, parsed)
        
        if result:
            print(f"  ✓ Analysis complete")
            print(f"    Score: {result.get('total_score')}/21")
            print(f"    Tier: {result.get('tier')}")
            
            # Update database
            cursor.execute("""
                UPDATE website_analysis 
                SET 
                    parsed_content = ?,
                    total_score = ?,
                    tier = ?,
                    proceed_to_stage_2 = ?,
                    category_scores = ?,
                    exceptional_signals = ?,
                    missing_elements = ?,
                    quick_assessment = ?,
                    stage_2_links = ?,
                    reasoning = ?,
                    analyzed_at = ?
                WHERE ticker = ?
            """, (
                json.dumps(parsed),
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
            
            # Show results
            signals = result.get('exceptional_signals', [])
            if signals:
                print(f"    Positive: {len(signals)} signals")
                for s in signals[:2]:
                    print(f"      • {s}")
            
            missing = result.get('missing_elements', [])
            if missing:
                print(f"    Missing: {len(missing)} elements")
                for m in missing[:2]:
                    print(f"      • {m}")
        else:
            print("  ❌ Analysis failed")
        
        if i < 4:
            time.sleep(3)
    
    # Summary
    print("\n" + "="*80)
    print("📊 FINAL RESULTS")
    print("="*80)
    
    cursor.execute("""
        SELECT ticker, total_score, tier, proceed_to_stage_2
        FROM website_analysis
        WHERE ticker IN ('GAI', 'MSIA', 'STRAT', 'REX')
        ORDER BY total_score DESC
    """)
    
    for row in cursor.fetchall():
        ticker, score, tier, stage2 = row
        print(f"{ticker}: {score}/21 ({tier}) - Stage 2: {'✅' if stage2 else '❌'}")
    
    conn.close()
    print("\n✅ Done! Check http://localhost:5006")

if __name__ == "__main__":
    main()