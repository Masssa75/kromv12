#!/usr/bin/env python3
"""
Batch analyzer using Gemini API instead of OpenRouter
"""

import os
import json
import time
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client
import google.generativeai as genai

# Load environment variables
load_dotenv('../.env')

# Configure Gemini
GEMINI_API_KEY = 'AIzaSyBFtSMQzyOZXYuHeLvJzu4bj8uIiBR_0DU'
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

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

def analyze_website_content(url, content_text):
    """Analyze website content using Gemini"""
    
    prompt = f"""Analyze this crypto project website and provide a JSON response.

URL: {url}
CONTENT (first 3000 chars): {content_text[:3000]}

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
- 3: Excellent/Exceptional

Focus on: GitHub repos, documentation, whitepapers, team info, real utility."""

    try:
        response = model.generate_content(prompt)
        text = response.text
        
        # Extract JSON from response
        import re
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            return json.loads(json_match.group(0))
    except Exception as e:
        print(f"    Gemini error: {str(e)[:100]}")
    
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

def simple_parse_website(url):
    """Simple website parser using requests"""
    import requests
    from bs4 import BeautifulSoup
    
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

def main():
    print("=" * 80)
    print("TOKEN DISCOVERY ANALYSIS - GEMINI BATCH")
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
    
    # Limit to top 10 for testing
    tokens_to_analyze = tokens_to_analyze[:10]
    print(f"\n🚀 Analyzing top {len(tokens_to_analyze)} tokens")
    
    analyzed_count = 0
    failed_count = 0
    
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
                
                # Analyze with Gemini
                print("  🤖 Analyzing with Gemini...")
                analysis = analyze_website_content(url, content)
                
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
        
        # Rate limit (Gemini allows 15 requests/minute)
        time.sleep(4)
    
    print("\n" + "=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)
    print(f"✅ Analyzed: {analyzed_count}")
    print(f"❌ Failed: {failed_count}")
    print(f"\nView results at: http://localhost:5007")

if __name__ == "__main__":
    main()