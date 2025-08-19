#!/usr/bin/env python3
"""
Fast hybrid analyzer - uses simple requests when possible, falls back to Playwright
"""

import sqlite3
import requests
import json
import time
from datetime import datetime
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('../.env')

OPENROUTER_API_KEY = os.getenv('OPEN_ROUTER_API_KEY', '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')

def fetch_simple(url, timeout=5):
    """Try simple HTTP request first"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=timeout)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style", "noscript"]):
                script.decompose()
            
            # Get text
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            if len(text) > 100:
                return text[:10000]
    except:
        pass
    return None

def analyze_with_ai(ticker, url, website_content):
    """Analyze website content using AI"""
    
    prompt = f"""Analyze this crypto project website for investment potential. Score each category 0-3:

TOKEN: {ticker}
URL: {url}
WEBSITE CONTENT (first 3000 chars):
{website_content[:3000]}

SCORING (0-3 each):
1. PROJECT: 0=meme only, 1=basic meme, 2=unclear utility, 3=clear utility/DeFi
2. TEAM: 0=none, 1=pseudonyms, 2=some info, 3=full team/LinkedIn
3. DOCS: 0=none, 1=basic, 2=detailed, 3=comprehensive whitepaper
4. COMMUNITY: 0=none, 1=basic socials, 2=active, 3=large engaged (10k+)
5. PARTNERS: 0=none, 1=unverified, 2=small verified, 3=major brands
6. TECH: 0=none, 1=basic contract, 2=GitHub/roadmap, 3=audits/testnet
7. TOKENOMICS: 0=none, 1=basic, 2=clear, 3=detailed vesting/utility

Respond EXACTLY:
SCORES: [proj,team,docs,comm,part,tech,token]
TOTAL: X/21
TIER: [TRASH/BASIC/SOLID/ALPHA]
PROCEED: [YES/NO]
SUMMARY: [One sentence]"""

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
                "max_tokens": 300
            },
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            
            parsed = {}
            for line in ai_response.split('\n'):
                if line.startswith('SCORES:'):
                    scores_str = line.replace('SCORES:', '').strip().strip('[]')
                    try:
                        scores = [int(s.strip()) for s in scores_str.split(',')]
                        parsed['scores'] = scores
                    except:
                        parsed['scores'] = [0] * 7
                elif line.startswith('TOTAL:'):
                    try:
                        total = int(line.split(':')[1].split('/')[0].strip())
                        parsed['total'] = total
                    except:
                        pass
                elif line.startswith('TIER:'):
                    parsed['tier'] = line.split(':')[1].strip()
                elif line.startswith('PROCEED:'):
                    parsed['proceed'] = line.split(':')[1].strip() == 'YES'
                elif line.startswith('SUMMARY:'):
                    parsed['summary'] = line.split(':', 1)[1].strip()
            
            # Defaults
            if 'total' not in parsed and 'scores' in parsed:
                parsed['total'] = sum(parsed['scores'])
            if 'tier' not in parsed:
                score = parsed.get('total', 0)
                parsed['tier'] = 'ALPHA' if score >= 15 else 'SOLID' if score >= 10 else 'BASIC' if score >= 5 else 'TRASH'
            if 'proceed' not in parsed:
                parsed['proceed'] = parsed.get('total', 0) >= 10
                
            return parsed
    except:
        pass
    return None

def get_unanalyzed_tokens():
    """Get tokens that haven't been analyzed yet"""
    conn = sqlite3.connect('token_discovery_analysis.db')
    cursor = conn.cursor()
    
    # Get already analyzed
    cursor.execute("SELECT ticker FROM website_analysis")
    analyzed = {row[0] for row in cursor.fetchall()}
    
    # Get from Supabase
    import subprocess
    result = subprocess.run([
        'curl', '-s',
        'https://eucfoommxxvqmmwdbkdv.supabase.co/rest/v1/token_discovery?select=symbol,website_url,initial_liquidity_usd&website_url=not.is.null&order=initial_liquidity_usd.desc&limit=300',
        '-H', 'apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Rika2R2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzU2Mjg4MSwiZXhwIjoyMDYzMTM4ODgxfQ.VcC7Bp3zMFYor3eVDonoG7BuS7AavemQnSOhrWcY5Y4'
    ], capture_output=True, text=True)
    
    try:
        tokens = json.loads(result.stdout)
        if isinstance(tokens, list):
            unanalyzed = [t for t in tokens if t['symbol'] not in analyzed]
            conn.close()
            return unanalyzed
    except:
        pass
    
    conn.close()
    return []

def save_analysis(ticker, url, analysis_result):
    """Save analysis results"""
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
            ticker, url,
            analysis_result.get('total', 0),
            analysis_result.get('tier', 'UNKNOWN'),
            analysis_result.get('proceed', False),
            'NONE',
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
            ticker, url, 0, 'FAILED', False,
            'Failed to analyze', 'Analysis failed',
            json.dumps([0]*7),
            datetime.now().isoformat(),
            False
        ))
    
    conn.commit()
    conn.close()

def main():
    """Main processing loop"""
    print("🚀 Fast Hybrid Analyzer")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tokens = get_unanalyzed_tokens()
    print(f"📊 Found {len(tokens)} unanalyzed tokens")
    
    if not tokens:
        print("✅ All tokens analyzed!")
        return
    
    # Process all remaining
    success = 0
    fail = 0
    stage2 = 0
    
    for i, token in enumerate(tokens, 1):
        ticker = token['symbol']
        url = token['website_url']
        liquidity = token.get('initial_liquidity_usd', 0)
        
        print(f"\n[{i}/{len(tokens)}] {ticker} - ${liquidity:,.0f}")
        
        # Try simple fetch first
        content = fetch_simple(url)
        
        if content:
            print(f"  ✅ Got {len(content)} chars")
            
            # Analyze
            analysis = analyze_with_ai(ticker, url, content)
            
            if analysis:
                score = analysis.get('total', 0)
                tier = analysis.get('tier', 'UNKNOWN')
                
                print(f"  📊 Score: {score}/21 - {tier}")
                if analysis.get('proceed'):
                    print(f"  🎯 STAGE 2 QUALIFIED!")
                    stage2 += 1
                
                save_analysis(ticker, url, analysis)
                success += 1
            else:
                print(f"  ❌ AI failed")
                save_analysis(ticker, url, None)
                fail += 1
        else:
            print(f"  ❌ Fetch failed")
            save_analysis(ticker, url, None)
            fail += 1
        
        # Quick rate limit
        time.sleep(1)
        
        # Progress update every 10
        if i % 10 == 0:
            print(f"\n--- Progress: {i}/{len(tokens)} - Success: {success}, Fail: {fail}, Stage2: {stage2} ---\n")
    
    print(f"\n✅ COMPLETE!")
    print(f"   Analyzed: {success}")
    print(f"   Failed: {fail}")
    print(f"   Stage 2: {stage2}")
    print(f"📊 View at http://localhost:5007")

if __name__ == "__main__":
    main()