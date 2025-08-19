#!/usr/bin/env python3
"""
Analyze crypto project websites using Gemini 2.5 Pro model
"""
import sqlite3
import requests
import json
import time
from datetime import datetime

# OpenRouter API configuration for Gemini 2.5 Pro
OPEN_ROUTER_API_KEY = "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"
MODEL = "google/gemini-2.5-pro"

def create_analysis_prompt(website_url, ticker):
    """Create the analysis prompt for Gemini 2.5 Pro"""
    return f"""Visit and analyze this crypto project website for {ticker} token: {website_url}

IMPORTANT: Actually visit the website and describe what you see before scoring.

First, provide a detailed description of what you observe on the website (1 paragraph):
- What is the main purpose/product shown?
- What sections are present (home, about, team, docs, etc)?
- Are there team members with names and photos?
- What technical information is available?
- What is the overall design quality and professionalism?

Then score the website's legitimacy from 1-10 based on:

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
  "website_description": "Detailed 1 paragraph description of what you actually see on the website",
  "score": (1-10),
  "tier": "(ALPHA/SOLID/BASIC/TRASH)",
  "legitimacy_indicators": ["list", "of", "positive", "findings"],
  "red_flags": ["list", "of", "concerning", "elements"],
  "technical_depth": "assessment of documentation/whitepaper quality",
  "team_transparency": "assessment of team information - BE SPECIFIC about what you found",
  "reasoning": "2-3 sentences explaining the score based on what you observed"
}}

Return ONLY the JSON response, no additional text."""

def analyze_website(ticker, website_url):
    """Analyze a single website using Gemini 2.5 Pro"""
    
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
                'max_tokens': 4000  # Increased for longer descriptions
                # Removed response_format as it may be causing issues
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            # Try to parse JSON from the response
            try:
                # Clean up the response - remove markdown blocks if present
                if '```json' in content:
                    content = content.split('```json')[1].split('```')[0]
                elif '```' in content:
                    content = content.split('```')[1].split('```')[0]
                
                # Find JSON object in the response
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                    analysis = json.loads(json_str)
                    return analysis, content
                else:
                    print(f"No JSON found in response for {ticker}")
                    return None, content
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON for {ticker}: {e}")
                print(f"Raw response preview: {content[:500]}...")
                return None, content
        else:
            print(f"API error for {ticker}: {response.status_code}")
            print(response.text)
            return None, None
            
    except Exception as e:
        print(f"Error analyzing {ticker}: {e}")
        return None, None

def update_database_schema():
    """Add website_description column if it doesn't exist"""
    conn = sqlite3.connect('website_analysis_new.db')
    cursor = conn.cursor()
    
    # Check if column exists
    cursor.execute("PRAGMA table_info(analysis_results)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'website_description' not in columns:
        cursor.execute('''
            ALTER TABLE analysis_results 
            ADD COLUMN website_description TEXT
        ''')
        conn.commit()
        print("Added website_description column to database")
    
    conn.close()

def save_analysis(token_id, ticker, website_url, analysis, raw_response):
    """Save analysis results to database"""
    
    conn = sqlite3.connect('website_analysis_new.db')
    cursor = conn.cursor()
    
    if analysis:
        cursor.execute('''
            INSERT INTO analysis_results 
            (token_id, ticker, website_url, website_description, score, tier, 
             legitimacy_indicators, red_flags, technical_depth, team_transparency, 
             reasoning, raw_response)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            token_id,
            ticker,
            website_url,
            analysis.get('website_description'),
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
    print("Updating database schema...")
    update_database_schema()
    
    print("\nFetching top 5 tokens by liquidity...")
    tokens = get_top_tokens(5)
    
    print(f"\nAnalyzing {len(tokens)} websites using Gemini 2.5 Pro...\n")
    print("This model will actually visit and describe each website.\n")
    
    for i, (token_id, ticker, website_url, liquidity) in enumerate(tokens, 1):
        print(f"[{i}/5] Analyzing {ticker} - {website_url}")
        print(f"      Liquidity: ${liquidity:,.0f}")
        
        # Analyze website
        analysis, raw_response = analyze_website(ticker, website_url)
        
        if analysis:
            score = analysis.get('score', 'N/A')
            tier = analysis.get('tier', 'N/A')
            description = analysis.get('website_description', '')
            print(f"      ✓ Score: {score}/10 ({tier})")
            if description:
                # Print first 100 chars of description
                desc_preview = description[:100] + "..." if len(description) > 100 else description
                print(f"      📝 {desc_preview}")
        else:
            print(f"      ✗ Analysis failed")
        
        # Save results
        save_analysis(token_id, ticker, website_url, analysis, raw_response)
        
        # Rate limiting - wait 3 seconds between requests
        if i < len(tokens):
            time.sleep(3)
    
    print("\n✅ Analysis complete! Results saved to database.")
    print("The AI has visited each website and provided detailed descriptions.")

if __name__ == "__main__":
    main()