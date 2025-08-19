#!/usr/bin/env python3
"""
Resilient Playwright-based analyzer with aggressive timeout handling
"""

import sqlite3
import json
import time
from datetime import datetime
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
import requests
import signal
from contextlib import contextmanager

# API Key
OPENROUTER_API_KEY = "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"

class TimeoutException(Exception):
    pass

@contextmanager
def timeout(seconds):
    """Context manager for timeout"""
    def signal_handler(signum, frame):
        raise TimeoutException("Operation timed out")
    
    signal.signal(signal.SIGALRM, signal_handler)
    signal.alarm(seconds)
    try:
        yield
    finally:
        signal.alarm(0)

def fetch_with_playwright(url, max_wait=15000):
    """Fetch website content using Playwright with strict timeouts"""
    content = None
    
    try:
        with timeout(20):  # Hard timeout at 20 seconds
            with sync_playwright() as p:
                browser = p.chromium.launch(
                    headless=True,
                    args=['--disable-blink-features=AutomationControlled']
                )
                
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                
                page = context.new_page()
                
                # Set page timeout
                page.set_default_timeout(max_wait)
                
                try:
                    # Navigate with networkidle
                    page.goto(url, wait_until='domcontentloaded', timeout=max_wait)
                    
                    # Wait a bit for JavaScript
                    page.wait_for_timeout(2000)
                    
                    # Get text content
                    content = page.evaluate("""
                        () => {
                            // Remove scripts and styles
                            const scripts = document.querySelectorAll('script, style, noscript');
                            scripts.forEach(el => el.remove());
                            
                            // Get text
                            return document.body ? document.body.innerText : document.documentElement.innerText;
                        }
                    """)
                    
                    if not content or len(content) < 100:
                        # Try getting all text if body is empty
                        content = page.inner_text('body')
                    
                except PlaywrightTimeout:
                    print(f"  ⏱️ Page timeout, extracting what we have...")
                    try:
                        content = page.inner_text('body')
                    except:
                        content = None
                
                browser.close()
                
    except TimeoutException:
        print(f"  ⏱️ Hard timeout reached")
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:100]}")
    
    if content:
        print(f"  ✅ Got {len(content)} chars")
    else:
        print(f"  ❌ Failed to get content")
    
    return content

def analyze_with_ai(ticker, url, website_content):
    """Analyze website content using AI"""
    
    prompt = f"""Analyze this crypto project website for investment potential. Score each category 0-3:

TOKEN: {ticker}
URL: {url}
WEBSITE CONTENT:
{website_content[:5000]}

SCORING CRITERIA (0-3 for each):
1. PROJECT CATEGORY (0-3):
   - 0: No clear purpose (meme/joke only)
   - 1: Basic meme with community focus
   - 2: Utility token with unclear use case
   - 3: Clear utility/infrastructure/DeFi/Gaming

2. TEAM & TRANSPARENCY (0-3):
   - 0: No team info at all
   - 1: Pseudonyms only
   - 2: Some team info/social links
   - 3: Full team with LinkedIn/experience

3. DOCUMENTATION (0-3):
   - 0: No docs/whitepaper
   - 1: Basic info/one-pager
   - 2: Detailed docs/litepaper
   - 3: Comprehensive whitepaper/gitbook

4. COMMUNITY & SOCIAL (0-3):
   - 0: No social links
   - 1: Basic Twitter/Telegram
   - 2: Active socials with engagement
   - 3: Large, engaged community (10k+ members)

5. PARTNERSHIPS & ADOPTION (0-3):
   - 0: No partnerships
   - 1: Claimed but unverified partnerships
   - 2: Verified small partnerships
   - 3: Major brand/protocol partnerships

6. TECHNICAL INFRASTRUCTURE (0-3):
   - 0: No technical info
   - 1: Basic contract info only
   - 2: GitHub/technical roadmap
   - 3: Active development/audits/testnet

7. TOKENOMICS & ROADMAP (0-3):
   - 0: No tokenomics/roadmap
   - 1: Basic supply info
   - 2: Clear tokenomics & roadmap
   - 3: Detailed vesting/utility/milestones

Respond in this EXACT format:
SCORES: [cat,team,docs,comm,part,tech,token]
TOTAL: X/21
TIER: [TRASH/BASIC/SOLID/ALPHA]
PROCEED: [YES/NO]
SIGNALS: [List any extraordinary signals or NONE]
SUMMARY: [One sentence summary]"""

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "moonshotai/kimi-k2",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.3,
                "max_tokens": 500
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            
            # Parse response
            parsed = {}
            lines = ai_response.strip().split('\n')
            
            for line in lines:
                try:
                    if line.startswith('SCORES:'):
                        scores_str = line.replace('SCORES:', '').strip().strip('[]')
                        scores = [int(s.strip()) for s in scores_str.split(',')]
                        parsed['scores'] = scores
                    elif line.startswith('TOTAL:'):
                        total = int(line.split(':')[1].split('/')[0].strip())
                        parsed['total'] = total
                    elif line.startswith('TIER:'):
                        parsed['tier'] = line.split(':')[1].strip()
                    elif line.startswith('PROCEED:'):
                        parsed['proceed'] = line.split(':')[1].strip() == 'YES'
                    elif line.startswith('SIGNALS:'):
                        parsed['signals'] = line.split(':', 1)[1].strip()
                    elif line.startswith('SUMMARY:'):
                        parsed['summary'] = line.split(':', 1)[1].strip()
                except:
                    continue
            
            # Set defaults
            if 'total' not in parsed and 'scores' in parsed:
                parsed['total'] = sum(parsed['scores'])
            if 'tier' not in parsed:
                score = parsed.get('total', 0)
                if score >= 15:
                    parsed['tier'] = 'ALPHA'
                elif score >= 10:
                    parsed['tier'] = 'SOLID'
                elif score >= 5:
                    parsed['tier'] = 'BASIC'
                else:
                    parsed['tier'] = 'TRASH'
            if 'proceed' not in parsed:
                parsed['proceed'] = parsed.get('total', 0) >= 10
                
            return parsed
        else:
            print(f"  AI API error: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"  AI analysis error: {str(e)[:100]}")
        return None

def get_unanalyzed_tokens():
    """Get tokens that haven't been analyzed yet"""
    conn = sqlite3.connect('token_discovery_analysis.db')
    cursor = conn.cursor()
    
    # Get already analyzed tokens
    cursor.execute("SELECT ticker FROM website_analysis")
    analyzed_tickers = {row[0] for row in cursor.fetchall()}
    
    # Get tokens from Supabase
    import subprocess
    result = subprocess.run([
        'curl', '-s',
        'https://eucfoommxxvqmmwdbkdv.supabase.co/rest/v1/token_discovery?select=symbol,website_url,network,initial_liquidity_usd&website_url=not.is.null&order=initial_liquidity_usd.desc',
        '-H', 'apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Ria2R2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzU2Mjg4MSwiZXhwIjoyMDYzMTM4ODgxfQ.VcC7Bp3zMFYor3eVDonoG7BuS7AavemQnSOhrWcY5Y4'
    ], capture_output=True, text=True)
    
    try:
        tokens = json.loads(result.stdout)
        if isinstance(tokens, list):
            unanalyzed = [t for t in tokens if t['symbol'] not in analyzed_tickers]
            conn.close()
            return unanalyzed
    except:
        pass
    
    conn.close()
    return []

def save_analysis(ticker, url, analysis_result):
    """Save analysis results to database"""
    conn = sqlite3.connect('token_discovery_analysis.db')
    cursor = conn.cursor()
    
    if analysis_result:
        scores = analysis_result.get('scores', [0]*7)
        
        cursor.execute('''
            INSERT OR REPLACE INTO website_analysis 
            (ticker, url, total_score, tier, proceed_to_stage_2, exceptional_signals, 
             quick_assessment, category_scores, analyzed_at, parse_success)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ticker,
            url,
            analysis_result.get('total', 0),
            analysis_result.get('tier', 'UNKNOWN'),
            analysis_result.get('proceed', False),
            analysis_result.get('signals', 'NONE'),
            analysis_result.get('summary', ''),
            json.dumps(scores),
            datetime.now().isoformat(),
            True
        ))
    else:
        cursor.execute('''
            INSERT OR REPLACE INTO website_analysis 
            (ticker, url, total_score, tier, proceed_to_stage_2, exceptional_signals, 
             quick_assessment, category_scores, analyzed_at, parse_success)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            ticker,
            url,
            0,
            'FAILED',
            False,
            'Failed to analyze',
            'Analysis failed',
            json.dumps([0]*7),
            datetime.now().isoformat(),
            False
        ))
    
    conn.commit()
    conn.close()

def main():
    """Main processing loop"""
    print("🚀 Starting Resilient Playwright Analyzer")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Get unanalyzed tokens
    tokens = get_unanalyzed_tokens()
    print(f"📊 Found {len(tokens)} unanalyzed tokens")
    
    # Process more tokens
    batch_size = 20
    success_count = 0
    fail_count = 0
    stage2_count = 0
    
    for i, token in enumerate(tokens[:batch_size], 1):
        ticker = token['symbol']
        url = token['website_url']
        liquidity = token.get('initial_liquidity_usd', 0)
        
        print(f"\n[{i}/{min(batch_size, len(tokens))}] {ticker} - ${liquidity:,.0f} liquidity")
        print(f"  URL: {url}")
        
        # Fetch website content
        content = fetch_with_playwright(url)
        
        if content and len(content) > 100:
            # Analyze with AI
            print("  🤖 Analyzing with AI...")
            analysis = analyze_with_ai(ticker, url, content)
            
            if analysis:
                score = analysis.get('total', 0)
                tier = analysis.get('tier', 'UNKNOWN')
                proceed = analysis.get('proceed', False)
                
                print(f"  ✅ Score: {score}/21 - Tier: {tier}")
                if proceed:
                    print(f"  🎯 QUALIFIES FOR STAGE 2!")
                    stage2_count += 1
                
                save_analysis(ticker, url, analysis)
                success_count += 1
            else:
                print(f"  ❌ AI analysis failed")
                save_analysis(ticker, url, None)
                fail_count += 1
        else:
            print(f"  ❌ Failed to fetch content")
            save_analysis(ticker, url, None)
            fail_count += 1
        
        # Rate limiting
        time.sleep(2)
    
    print(f"\n✅ Complete!")
    print(f"   Success: {success_count}")
    print(f"   Failed: {fail_count}")
    print(f"   Stage 2 qualified: {stage2_count}")
    print(f"📊 View results at http://localhost:5007")

if __name__ == "__main__":
    main()