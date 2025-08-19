#!/usr/bin/env python3
"""
Simple batch analyzer using OpenRouter API directly (no Playwright)
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

# Load environment variables
load_dotenv('../.env')

# OpenRouter API key
API_KEY = "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"

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
    except:
        return set()

def simple_parse_website(url):
    """Parse website with simple requests"""
    try:
        response = requests.get(url, timeout=10, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        return text[:5000]  # First 5000 chars
    except Exception as e:
        print(f"    Parse error: {str(e)[:50]}")
        return ""

def analyze_with_openrouter(url, content):
    """Analyze website content using OpenRouter API"""
    
    prompt = f"""Analyze this crypto project website and provide a JSON response.

URL: {url}
CONTENT (first 3000 chars): {content[:3000]}

Provide ONLY a JSON response with this exact structure:
{{
    "total_score": <sum of all category scores, max 21>,
    "proceed_to_stage_2": <true if total_score >= 10>,
    "category_scores": {{
        "technical_infrastructure": <0-3>,
        "business_utility": <0-3>,
        "documentation_quality": <0-3>,
        "community_social": <0-3>,
        "security_trust": <0-3>,
        "team_transparency": <0-3>,
        "website_presentation": <0-3>
    }},
    "exceptional_signals": [<list of positive findings>],
    "missing_elements": [<list of missing critical elements>],
    "automatic_stage_2_qualifiers": [<exceptional features if any>]
}}

Scoring guide (0-3 per category):
- 0: Missing/Poor
- 1: Basic/Minimal
- 2: Good/Standard
- 3: Excellent/Exceptional"""

    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {API_KEY}',
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
            
            # Extract JSON
            import re
            json_match = re.search(r'\{.*\}', ai_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
        else:
            print(f"    API error: {response.status_code}")
    except Exception as e:
        print(f"    Analysis error: {str(e)[:100]}")
    
    return None

def save_to_database(token_data, analysis):
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
            json.dumps({'content': token_data.get('content_text', '')}),
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
    except Exception as e:
        print(f"    DB error: {e}")
    finally:
        conn.close()

def main():
    print("=" * 80)
    print("SIMPLE TOKEN DISCOVERY ANALYSIS - OPENROUTER")
    print("=" * 80)
    
    # Get already analyzed
    already_analyzed = get_already_analyzed()
    print(f"Already analyzed: {len(already_analyzed)} tokens")
    
    # Fetch tokens
    print("Fetching tokens from Supabase...")
    response = supabase.table('token_discovery').select(
        'contract_address, symbol, network, website_url, initial_liquidity_usd'
    ).not_.is_('website_url', 'null').order('initial_liquidity_usd', desc=True).execute()
    
    tokens = response.data
    print(f"Total tokens with websites: {len(tokens)}")
    
    # Filter new ones
    tokens_to_analyze = [t for t in tokens if t['symbol'] not in already_analyzed]
    print(f"Tokens to analyze: {len(tokens_to_analyze)}")
    
    if not tokens_to_analyze:
        print("✅ All tokens already analyzed!")
        return
    
    print(f"\n🚀 Analyzing {len(tokens_to_analyze)} tokens")
    print("Estimated time: ~15 seconds per token")
    print(f"Total time: ~{len(tokens_to_analyze) * 15 / 60:.1f} minutes")
    
    analyzed_count = 0
    failed_count = 0
    start_time = time.time()
    
    for i, token in enumerate(tokens_to_analyze, 1):
        symbol = token['symbol']
        url = token['website_url']
        liquidity = token.get('initial_liquidity_usd', 0) or 0
        
        print(f"\n[{i}/{len(tokens_to_analyze)}] {symbol}")
        print(f"  URL: {url}")
        print(f"  Liquidity: ${liquidity:,.0f}")
        
        try:
            # Parse website
            print("  📝 Parsing website...")
            content = simple_parse_website(url)
            
            if content:
                print(f"  ✅ Parsed {len(content)} characters")
                token['content_text'] = content
                
                # Analyze with OpenRouter
                print("  🤖 Analyzing with Kimi K2...")
                analysis = analyze_with_openrouter(url, content)
                
                if analysis:
                    score = analysis.get('total_score', 0)
                    stage2 = analysis.get('proceed_to_stage_2', False)
                    print(f"  📊 Score: {score}/21")
                    print(f"  🎯 Stage 2: {'YES' if stage2 else 'NO'}")
                    
                    # Save to database
                    save_to_database(token, analysis)
                    analyzed_count += 1
                else:
                    print("  ⚠️ No analysis returned")
                    failed_count += 1
            else:
                print("  ❌ Failed to parse website")
                failed_count += 1
                
        except Exception as e:
            print(f"  ❌ Error: {str(e)[:100]}")
            failed_count += 1
        
        # Rate limit
        time.sleep(2)
        
        # Progress update every 10 tokens
        if i % 10 == 0:
            elapsed = time.time() - start_time
            avg_time = elapsed / i
            remaining = (len(tokens_to_analyze) - i) * avg_time
            print(f"\n⏱️  Progress: {i}/{len(tokens_to_analyze)} - Est. {remaining/60:.1f} min remaining")
    
    elapsed_time = time.time() - start_time
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"✅ Analyzed: {analyzed_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"⏱️ Time: {elapsed_time/60:.1f} minutes")
    print(f"\nView results at: http://localhost:5007")

if __name__ == "__main__":
    main()