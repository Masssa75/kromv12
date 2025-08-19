#!/usr/bin/env python3
"""
Analyze crypto project websites using Kimi K2 model
"""
import sqlite3
import requests
import json
import time
from datetime import datetime

# OpenRouter API configuration
OPEN_ROUTER_API_KEY = "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"
MODEL = "moonshotai/kimi-k2"

def create_analysis_prompt(website_url, ticker):
    """Create the analysis prompt for Kimi K2"""
    return f"""Analyze this crypto project website for {ticker} token: {website_url}

Score the website's legitimacy from 1-10 based on:

SCORING CRITERIA:
8-10: ALPHA - Enterprise-grade with verifiable backing
- Real team with LinkedIn profiles and photos
- Working product/demo available
- Audited smart contracts
- Clear technical documentation/whitepaper
- Verifiable partnerships or investors

6-7: SOLID - Professional project site
- Clear roadmap and vision
- Some team information visible
- Active development updates
- Decent documentation
- Professional design

4-5: BASIC - Minimal but functional
- Template-based but customized
- Limited technical details
- Some effort shown
- Basic information present

1-3: TRASH - Red flags present
- Generic template with no customization
- Vague promises or unrealistic claims
- No team information
- Pump rhetoric
- Poor grammar/spelling

Provide your analysis as JSON with these fields:
{{
  "score": (1-10),
  "tier": "(ALPHA/SOLID/BASIC/TRASH)",
  "legitimacy_indicators": ["list", "of", "positive", "findings"],
  "red_flags": ["list", "of", "concerning", "elements"],
  "technical_depth": "assessment of documentation/whitepaper quality",
  "team_transparency": "assessment of team information",
  "reasoning": "2-3 sentences explaining the score"
}}

Return ONLY the JSON response, no additional text."""

def analyze_website(ticker, website_url):
    """Analyze a single website using Kimi K2"""
    
    prompt = create_analysis_prompt(website_url, ticker)
    
    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers={
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {OPEN_ROUTER_API_KEY}',
            },
            json={
                'model': MODEL,
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': 0.1,
                'max_tokens': 1000
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Try to parse JSON from the response
            try:
                # Remove any markdown code blocks if present
                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0]
                elif '```' in content:
                    content = content.split('```')[1].split('```')[0]
                
                analysis = json.loads(content.strip())
                return analysis, content
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON for {ticker}: {e}")
                print(f"Raw response: {content}")
                return None, content
        else:
            print(f"API error for {ticker}: {response.status_code}")
            print(response.text)
            return None, None
            
    except Exception as e:
        print(f"Error analyzing {ticker}: {e}")
        return None, None

def save_analysis(token_id, ticker, website_url, analysis, raw_response):
    """Save analysis results to database"""
    
    conn = sqlite3.connect('website_analysis_new.db')
    cursor = conn.cursor()
    
    if analysis:
        cursor.execute('''
            INSERT INTO analysis_results 
            (token_id, ticker, website_url, score, tier, legitimacy_indicators, 
             red_flags, technical_depth, team_transparency, reasoning, raw_response)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            token_id,
            ticker,
            website_url,
            analysis.get('score'),
            analysis.get('tier'),
            json.dumps(analysis.get('legitimacy_indicators', [])),
            json.dumps(analysis.get('red_flags', [])),
            analysis.get('technical_depth'),
            analysis.get('team_transparency'),
            analysis.get('reasoning'),
            raw_response
        ))
    else:
        # Save failed analysis
        cursor.execute('''
            INSERT INTO analysis_results 
            (token_id, ticker, website_url, raw_response)
            VALUES (?, ?, ?, ?)
        ''', (token_id, ticker, website_url, raw_response or "Analysis failed"))
    
    conn.commit()
    conn.close()

def get_top_tokens(limit=5):
    """Get top tokens by liquidity from database"""
    
    conn = sqlite3.connect('website_analysis_new.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, ticker, website_url, liquidity_usd
        FROM tokens
        WHERE liquidity_usd IS NOT NULL
        ORDER BY liquidity_usd DESC
        LIMIT ?
    ''', (limit,))
    
    tokens = cursor.fetchall()
    conn.close()
    
    return tokens

def main():
    print("Fetching top 5 tokens by liquidity...")
    tokens = get_top_tokens(5)
    
    print(f"\nAnalyzing {len(tokens)} websites using Kimi K2...\n")
    
    for i, (token_id, ticker, website_url, liquidity) in enumerate(tokens, 1):
        print(f"[{i}/5] Analyzing {ticker} - {website_url}")
        print(f"      Liquidity: ${liquidity:,.0f}")
        
        # Analyze website
        analysis, raw_response = analyze_website(ticker, website_url)
        
        if analysis:
            score = analysis.get('score', 'N/A')
            tier = analysis.get('tier', 'N/A')
            print(f"      ✓ Score: {score}/10 ({tier})")
        else:
            print(f"      ✗ Analysis failed")
        
        # Save results
        save_analysis(token_id, ticker, website_url, analysis, raw_response)
        
        # Rate limiting - wait 2 seconds between requests
        if i < len(tokens):
            time.sleep(2)
    
    print("\n✅ Analysis complete! Results saved to database.")

if __name__ == "__main__":
    main()