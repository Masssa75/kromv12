#!/usr/bin/env python3
"""
Batch analyzer using ScraperAPI for website parsing (instead of Playwright)
This solves the hanging issue and provides better JavaScript rendering
"""

import os
import json
import time
import sqlite3
import requests
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client
from bs4 import BeautifulSoup
import re

# Load environment variables
load_dotenv('../.env')

# API Keys
OPENROUTER_KEY = "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"
SCRAPERAPI_KEY = "43f3f4aa590f2d310b5a70d8a28e94a2"

# Initialize Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(supabase_url, supabase_key)

def get_already_analyzed():
    """Get list of already analyzed tokens"""
    try:
        conn = sqlite3.connect('token_discovery_analysis.db')
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS website_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT UNIQUE,
                url TEXT,
                network TEXT,
                contract_address TEXT,
                initial_liquidity_usd REAL,
                parsed_content TEXT,
                analysis_json TEXT,
                total_score INTEGER,
                proceed_to_stage_2 BOOLEAN,
                category_scores TEXT,
                exceptional_signals TEXT,
                missing_elements TEXT,
                automatic_stage_2_qualifiers TEXT,
                analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        
        cursor.execute("SELECT DISTINCT ticker FROM website_analysis")
        analyzed = {row[0] for row in cursor.fetchall()}
        conn.close()
        return analyzed
    except Exception as e:
        print(f"DB error: {e}")
        return set()

def parse_with_scraperapi(url):
    """Parse website using ScraperAPI for JavaScript rendering"""
    try:
        # ScraperAPI endpoint
        api_url = "http://api.scraperapi.com"
        
        params = {
            'api_key': SCRAPERAPI_KEY,
            'url': url,
            'render': 'true',  # Enable JavaScript rendering
            'wait_for_selector': 'body',  # Wait for body to load
            'timeout': '30000'  # 30 second timeout
        }
        
        print(f"    🌐 Fetching with ScraperAPI...")
        response = requests.get(api_url, params=params, timeout=35)
        
        if response.status_code == 200:
            # Parse HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get text content
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            # Also extract links for better analysis
            links = []
            for link in soup.find_all('a', href=True):
                href = link['href'].lower()
                link_text = link.get_text().strip()
                if any(keyword in href or keyword in link_text.lower() for keyword in 
                       ['github', 'docs', 'documentation', 'whitepaper', 'twitter', 'telegram', 'discord']):
                    links.append(f"{link_text}: {link['href']}")
            
            # Combine text and important links
            if links:
                text += "\n\nIMPORTANT LINKS:\n" + "\n".join(links[:20])
            
            return text[:8000]  # Return up to 8000 chars
        else:
            print(f"    ⚠️ ScraperAPI error: {response.status_code}")
            return ""
            
    except requests.Timeout:
        print(f"    ⚠️ ScraperAPI timeout")
        return ""
    except Exception as e:
        print(f"    ❌ Parse error: {str(e)[:100]}")
        return ""

def analyze_with_openrouter(url, content):
    """Analyze website content using OpenRouter API"""
    
    prompt = f"""Analyze this crypto project website content and provide a structured assessment.

URL: {url}
CONTENT (parsed with JavaScript rendering):
{content[:4000]}

Provide a JSON response with this EXACT structure:
{{
    "total_score": <integer, sum of all category scores, max 21>,
    "proceed_to_stage_2": <boolean, true if total_score >= 10>,
    "category_scores": {{
        "technical_infrastructure": <0-3>,
        "business_utility": <0-3>,
        "documentation_quality": <0-3>,
        "community_social": <0-3>,
        "security_trust": <0-3>,
        "team_transparency": <0-3>,
        "website_presentation": <0-3>
    }},
    "exceptional_signals": ["list of positive findings"],
    "missing_elements": ["list of critical missing elements"],
    "automatic_stage_2_qualifiers": ["exceptional features warranting deeper analysis"]
}}

Scoring criteria (0-3 per category):
- 3: Excellent (GitHub repos, extensive docs, clear team info, audits)
- 2: Good (standard documentation, social presence, basic info)
- 1: Minimal (basic website, limited information)
- 0: Missing or very poor

Focus on: GitHub/code repos, documentation, whitepapers, team information, real utility, security audits."""

    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {OPENROUTER_KEY}',
            },
            json={
                'model': 'moonshotai/kimi-k2',
                'messages': [{'role': 'user', 'content': prompt}],
                'temperature': 0.1,
                'max_tokens': 2000
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            ai_text = result['choices'][0]['message']['content']
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', ai_text, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group(0))
                return analysis
            else:
                print(f"    ⚠️ No JSON found in response")
                return None
        else:
            print(f"    ❌ API error: {response.status_code}")
            return None
            
    except json.JSONDecodeError as e:
        print(f"    ⚠️ JSON parse error: {str(e)[:50]}")
        return None
    except Exception as e:
        print(f"    ❌ Analysis error: {str(e)[:100]}")
        return None

def save_to_database(token_data, analysis, content):
    """Save analysis results to database"""
    conn = sqlite3.connect('token_discovery_analysis.db')
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            INSERT OR REPLACE INTO website_analysis 
            (ticker, url, network, contract_address, initial_liquidity_usd,
             parsed_content, analysis_json, total_score, proceed_to_stage_2,
             category_scores, exceptional_signals, missing_elements, 
             automatic_stage_2_qualifiers, analyzed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            token_data['symbol'],
            token_data['website_url'],
            token_data['network'],
            token_data['contract_address'],
            token_data.get('initial_liquidity_usd'),
            json.dumps({'content': content, 'scraperapi': True}),
            json.dumps(analysis),
            analysis.get('total_score', 0),
            analysis.get('proceed_to_stage_2', False),
            json.dumps(analysis.get('category_scores', {})),
            json.dumps(analysis.get('exceptional_signals', [])),
            json.dumps(analysis.get('missing_elements', [])),
            json.dumps(analysis.get('automatic_stage_2_qualifiers', [])),
            datetime.now()
        ))
        conn.commit()
        return True
    except Exception as e:
        print(f"    ❌ DB error: {e}")
        return False
    finally:
        conn.close()

def main():
    print("=" * 80)
    print("TOKEN DISCOVERY BATCH ANALYSIS - SCRAPERAPI + OPENROUTER")
    print("=" * 80)
    print("Using ScraperAPI for JavaScript rendering (no Playwright issues!)")
    print("=" * 80)
    
    # Get already analyzed
    already_analyzed = get_already_analyzed()
    print(f"\n📊 Already analyzed: {len(already_analyzed)} tokens")
    
    # Fetch tokens from Supabase
    print("📡 Fetching tokens from Supabase...")
    response = supabase.table('token_discovery').select(
        'contract_address, symbol, network, website_url, initial_liquidity_usd'
    ).not_.is_('website_url', 'null').order('initial_liquidity_usd', desc=True).execute()
    
    tokens = response.data
    print(f"📋 Total tokens with websites: {len(tokens)}")
    
    # Filter out already analyzed
    tokens_to_analyze = [t for t in tokens if t['symbol'] not in already_analyzed]
    print(f"🆕 New tokens to analyze: {len(tokens_to_analyze)}")
    
    if not tokens_to_analyze:
        print("\n✅ All tokens already analyzed!")
        return
    
    # Show top tokens
    print(f"\n🔝 Top 5 tokens to analyze:")
    for i, token in enumerate(tokens_to_analyze[:5], 1):
        liquidity = token.get('initial_liquidity_usd', 0) or 0
        print(f"  {i}. {token['symbol']:10} ${liquidity:>10,.0f} - {token['website_url'][:40]}")
    
    print(f"\n🚀 Starting analysis of {len(tokens_to_analyze)} tokens")
    print(f"⏱️  Estimated time: ~20 seconds per token")
    print(f"⏱️  Total time: ~{len(tokens_to_analyze) * 20 / 60:.1f} minutes")
    print("=" * 80)
    
    analyzed_count = 0
    failed_count = 0
    start_time = time.time()
    
    for i, token in enumerate(tokens_to_analyze, 1):
        symbol = token['symbol']
        url = token['website_url']
        liquidity = token.get('initial_liquidity_usd', 0) or 0
        
        print(f"\n[{i}/{len(tokens_to_analyze)}] {symbol}")
        print(f"  💰 Liquidity: ${liquidity:,.0f}")
        print(f"  🔗 URL: {url}")
        
        try:
            # Parse with ScraperAPI
            content = parse_with_scraperapi(url)
            
            if content and len(content) > 100:
                print(f"    ✅ Parsed {len(content)} characters")
                
                # Analyze with OpenRouter
                print(f"    🤖 Analyzing with Kimi K2...")
                analysis = analyze_with_openrouter(url, content)
                
                if analysis and analysis.get('total_score') is not None:
                    score = analysis.get('total_score', 0)
                    stage2 = analysis.get('proceed_to_stage_2', False)
                    
                    print(f"    📊 Score: {score}/21")
                    print(f"    🎯 Stage 2: {'✅ YES' if stage2 else '❌ NO'}")
                    
                    # Show category breakdown
                    if analysis.get('category_scores'):
                        cats = analysis['category_scores']
                        print(f"    📈 Categories: Tech:{cats.get('technical_infrastructure',0)} "
                              f"Biz:{cats.get('business_utility',0)} "
                              f"Docs:{cats.get('documentation_quality',0)} "
                              f"Team:{cats.get('team_transparency',0)}")
                    
                    # Save to database
                    if save_to_database(token, analysis, content):
                        analyzed_count += 1
                    else:
                        failed_count += 1
                else:
                    print(f"    ⚠️ No valid analysis returned")
                    failed_count += 1
            else:
                print(f"    ❌ Failed to parse website (got {len(content) if content else 0} chars)")
                failed_count += 1
                
        except Exception as e:
            print(f"    ❌ Error: {str(e)[:100]}")
            failed_count += 1
        
        # Rate limiting
        time.sleep(3)  # 3 seconds between requests
        
        # Progress update every 10 tokens
        if i % 10 == 0:
            elapsed = time.time() - start_time
            avg_time = elapsed / i
            remaining = (len(tokens_to_analyze) - i) * avg_time
            print(f"\n⏱️  Progress: {i}/{len(tokens_to_analyze)} - "
                  f"Success rate: {analyzed_count/i*100:.1f}% - "
                  f"Est. {remaining/60:.1f} min remaining")
    
    # Final summary
    elapsed_time = time.time() - start_time
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"✅ Successfully analyzed: {analyzed_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"📊 Success rate: {analyzed_count/(analyzed_count+failed_count)*100:.1f}%")
    print(f"⏱️  Total time: {elapsed_time/60:.1f} minutes")
    print(f"⚡ Avg time per token: {elapsed_time/len(tokens_to_analyze):.1f} seconds")
    print(f"\n🌐 View results at: http://localhost:5007")
    print(f"   (Server already running)")

if __name__ == "__main__":
    main()