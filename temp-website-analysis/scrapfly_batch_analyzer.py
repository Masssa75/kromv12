#!/usr/bin/env python3
import sqlite3
import requests
import json
import time
import os
from datetime import datetime

# ScrapFly API configuration
SCRAPFLY_API_KEY = "scp-live-2beb370f43d24c00b37aeba6514659d5"
OPENROUTER_API_KEY = "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"

def fetch_with_scrapfly(url):
    """Fetch website content using ScrapFly API"""
    print(f"  Fetching {url}...")
    api_url = "https://api.scrapfly.io/scrape"
    
    params = {
        "key": SCRAPFLY_API_KEY,
        "url": url,
        "render_js": "true",
        "wait_for_selector": "body",
        "timeout": 20000,
        "retry": "false",
        "country": "us",
        "format": "json"
    }
    
    try:
        response = requests.get(api_url, params=params, timeout=25)
        
        if response.status_code == 200:
            data = response.json()
            result = data.get("result", {})
            
            # Get the HTML content
            html_content = result.get("content", "")
            
            # Simple text extraction from HTML
            import re
            # Remove script and style tags completely
            html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL)
            html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
            # Remove HTML tags
            text = re.sub('<[^<]+?>', ' ', html_content)
            # Clean up whitespace
            text = re.sub(r'\s+', ' ', text).strip()
            
            return text[:10000]  # Limit to 10k chars for AI analysis
            
        else:
            print(f"ScrapFly error {response.status_code}: {response.text[:200]}")
            return None
            
    except requests.exceptions.Timeout:
        print(f"ScrapFly timeout for {url}")
        return None
    except Exception as e:
        print(f"ScrapFly error: {e}")
        return None

def analyze_with_ai(ticker, url, website_content):
    """Analyze website content using AI"""
    
    # Create analysis prompt
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

EXTRAORDINARY SIGNALS (Optional - list any):
- Major achievements ($10M+ funding, 100k+ users, etc)
- Red flags (security warnings, rug pull indicators)
- Unique value propositions

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
        
        if response.status_code != 200:
            print(f"  API Error {response.status_code}")
            return None
        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content']
            
            # Parse the response
            lines = ai_response.strip().split('\n')
            parsed = {}
            
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
                except Exception as e:
                    print(f"Error parsing line '{line}': {e}")
                    continue
            
            if not parsed:
                print(f"Failed to parse AI response. Full response: {ai_response}")
                return None
            
            # Ensure all required fields are present
            if 'total' not in parsed:
                parsed['total'] = 0
            if 'tier' not in parsed:
                parsed['tier'] = 'UNKNOWN'
            if 'proceed' not in parsed:
                parsed['proceed'] = False
            if 'signals' not in parsed:
                parsed['signals'] = 'NONE'
            if 'summary' not in parsed:
                parsed['summary'] = 'No summary available'
            if 'scores' not in parsed:
                parsed['scores'] = [0] * 7
            
            return parsed
            
    except Exception as e:
        print(f"AI analysis error: {str(e)[:200]}")
        import traceback
        traceback.print_exc()
        return None

def get_unanalyzed_tokens():
    """Get tokens that haven't been analyzed yet"""
    conn = sqlite3.connect('token_discovery_analysis.db')
    cursor = conn.cursor()
    
    # Get tokens from Supabase that aren't in our analysis DB
    import subprocess
    result = subprocess.run([
        'curl', '-s',
        'https://eucfoommxxvqmmwdbkdv.supabase.co/rest/v1/token_discovery?select=symbol,website_url,network,initial_liquidity_usd&website_url=not.is.null&order=initial_liquidity_usd.desc',
        '-H', f'apikey: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Ria2R2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzU2Mjg4MSwiZXhwIjoyMDYzMTM4ODgxfQ.VcC7Bp3zMFYor3eVDonoG7BuS7AavemQnSOhrWcY5Y4'
    ], capture_output=True, text=True)
    
    # Check if we got valid JSON
    if not result.stdout:
        print("No response from Supabase")
        return []
    
    try:
        tokens = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"Failed to parse JSON: {result.stdout[:200]}")
        return []
    
    # Filter out already analyzed tokens
    analyzed = cursor.execute("SELECT ticker FROM website_analysis").fetchall()
    analyzed_tickers = {row[0] for row in analyzed}
    
    # Make sure tokens is a list
    if isinstance(tokens, list):
        unanalyzed = [t for t in tokens if t['symbol'] not in analyzed_tickers]
    else:
        print(f"Unexpected response format: {type(tokens)}")
        unanalyzed = []
    
    conn.close()
    return unanalyzed

def save_analysis(ticker, url, network, analysis_result):
    """Save analysis results to database"""
    conn = sqlite3.connect('token_discovery_analysis.db')
    cursor = conn.cursor()
    
    if analysis_result:
        scores = analysis_result.get('scores', [0]*7)
        
        # Use existing schema columns
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
        # Save as failed attempt
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
    print("Starting ScrapFly batch analyzer...")
    
    # Get unanalyzed tokens
    tokens = get_unanalyzed_tokens()
    print(f"Found {len(tokens)} tokens to analyze")
    
    # Process each token
    success_count = 0
    fail_count = 0
    
    for i, token in enumerate(tokens[:5], 1):  # Start with 5 for testing
        ticker = token['symbol']
        url = token['website_url']
        network = token['network']
        liquidity = token.get('initial_liquidity_usd', 0)
        
        print(f"\n[{i}/{min(20, len(tokens))}] Analyzing {ticker} ({network}) - ${liquidity:,.0f} liquidity")
        print(f"  URL: {url}")
        
        # Fetch website content
        print("  Fetching content...")
        content = fetch_with_scrapfly(url)
        
        if content and len(content) > 100:
            print(f"  ✅ Got {len(content)} chars of content")
            
            # Analyze with AI
            print("  Analyzing with AI...")
            analysis = analyze_with_ai(ticker, url, content)
            
            if analysis:
                print(f"  ✅ Analysis complete: {analysis.get('total', 0)}/21 - {analysis.get('tier', 'UNKNOWN')}")
                if analysis.get('proceed'):
                    print(f"  🎯 QUALIFIES FOR STAGE 2!")
                save_analysis(ticker, url, network, analysis)
                success_count += 1
            else:
                print(f"  ❌ AI analysis failed")
                save_analysis(ticker, url, network, None)
                fail_count += 1
        else:
            print(f"  ❌ Failed to fetch content")
            save_analysis(ticker, url, network, None)
            fail_count += 1
        
        # Rate limiting
        time.sleep(2)
    
    print(f"\n✅ Complete! Success: {success_count}, Failed: {fail_count}")
    print(f"View results at http://localhost:5007")

if __name__ == "__main__":
    main()