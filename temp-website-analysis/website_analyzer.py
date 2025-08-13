#!/usr/bin/env python3
"""
Website Analysis Script using Kimi K2
Analyzes crypto project websites and stores results in local SQLite database
"""

import os
import sys
import json
import sqlite3
import time
from datetime import datetime
from typing import Dict, Any, Optional
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv('../.env')

# Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
OPEN_ROUTER_API_KEY = os.getenv('OPEN_ROUTER_API_KEY')

class WebsiteAnalyzer:
    def __init__(self):
        self.init_database()
        
    def init_database(self):
        """Initialize local SQLite database"""
        self.conn = sqlite3.connect('analysis_results.db')
        self.cursor = self.conn.cursor()
        
        # Create table if not exists
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS website_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                token_id TEXT UNIQUE,
                ticker TEXT,
                network TEXT,
                contract_address TEXT,
                website_url TEXT,
                website_score INTEGER,
                website_tier TEXT,
                project_category TEXT,
                has_real_utility BOOLEAN,
                utility_description TEXT,
                documentation_quality TEXT,
                team_transparency TEXT,
                has_audit BOOLEAN,
                has_whitepaper BOOLEAN,
                has_roadmap BOOLEAN,
                has_working_product BOOLEAN,
                red_flags TEXT,
                green_flags TEXT,
                key_findings TEXT,
                website_summary TEXT,
                analysis_json TEXT,
                analyzed_at TIMESTAMP,
                error_message TEXT
            )
        ''')
        
        # Add website_summary column if it doesn't exist (for existing databases)
        self.cursor.execute("PRAGMA table_info(website_analysis)")
        columns = [col[1] for col in self.cursor.fetchall()]
        if 'website_summary' not in columns:
            self.cursor.execute('ALTER TABLE website_analysis ADD COLUMN website_summary TEXT')
        
        self.conn.commit()
    
    def fetch_tokens_to_analyze(self, limit=20):
        """Fetch tokens from Supabase that have websites but no analysis"""
        headers = {
            'apikey': SUPABASE_SERVICE_ROLE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Query for tokens with websites
        query = '''
            select=id,ticker,contract_address,network,website_url,analysis_token_type,ath_roi_percent
            &website_url=not.is.null
            &website_analyzed_at=is.null
            &is_dead=is.false
            &is_invalidated=is.false
            &order=ath_roi_percent.desc.nullsfirst
            &limit={}
        '''.format(limit).replace('\n', '').replace('    ', '')
        
        url = f"{SUPABASE_URL}/rest/v1/crypto_calls?{query}"
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                tokens = response.json()
                print(f"Fetched {len(tokens)} tokens from Supabase")
                
                # Filter out already analyzed tokens
                analyzed_ids = self.get_analyzed_token_ids()
                new_tokens = [t for t in tokens if t['id'] not in analyzed_ids]
                print(f"Found {len(new_tokens)} tokens not yet analyzed locally")
                
                return new_tokens
            else:
                print(f"Error fetching from Supabase: {response.status_code}")
                print(response.text)
                return []
        except Exception as e:
            print(f"Error fetching tokens: {e}")
            return []
    
    def get_analyzed_token_ids(self):
        """Get list of token IDs already analyzed"""
        self.cursor.execute("SELECT token_id FROM website_analysis")
        return set(row[0] for row in self.cursor.fetchall())
    
    def analyze_website(self, token: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Analyze a website using Kimi K2"""
        website_url = token.get('website_url')
        if not website_url:
            return None
        
        prompt = f"""Visit and analyze this crypto project website: {website_url}

Token: {token.get('ticker', 'Unknown')} ({token.get('network', 'Unknown')})
Contract: {token.get('contract_address', 'Unknown')}

First, provide a detailed 1-paragraph summary describing what you actually see on the website - the main content, features, design, and any specific claims or information presented.

Then evaluate the following aspects:

1. Project legitimacy (1-10 score)
2. Documentation quality (whitepaper, docs, tokenomics)
3. Team transparency (visible team, KYC, anonymous)
4. Technical indicators (audit, roadmap, github)
5. Utility description (what does this token actually do?)
6. Red flags and green flags

Return a JSON object with the following structure:
{{
    "website_summary": "<detailed paragraph describing what's actually on the website>",
    "website_score": <1-10>,
    "website_tier": "<ALPHA|SOLID|BASIC|TRASH>",
    "project_category": "<defi|gaming|meme|utility|infrastructure|other>",
    "has_real_utility": <true|false>,
    "utility_description": "<brief description>",
    "documentation_quality": "<excellent|good|basic|poor|none>",
    "team_transparency": "<fully_visible|partial|anonymous|fake>",
    "has_audit": <true|false>,
    "has_whitepaper": <true|false>,
    "has_roadmap": <true|false>,
    "has_working_product": <true|false>,
    "red_flags": ["<flag1>", "<flag2>"],
    "green_flags": ["<flag1>", "<flag2>"],
    "key_findings": "<summary of findings>",
    "confidence": <0.0-1.0>
}}

Scoring guidelines:
- 9-10: ALPHA tier - Exceptional project with clear utility and strong fundamentals
- 7-8: SOLID tier - Good project with working product or clear roadmap
- 4-6: BASIC tier - Standard project, may lack some key elements
- 1-3: TRASH tier - Poor quality, likely scam or abandoned

Important: If the website is down, redirects to unrelated content, or appears to be a scam, score it 1 and set tier to TRASH."""

        headers = {
            'Authorization': f'Bearer {OPEN_ROUTER_API_KEY}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://github.com/KROMV12/website-analyzer',
            'X-Title': 'KROM Website Analyzer'
        }
        
        data = {
            'model': 'moonshotai/kimi-k2',
            'messages': [
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.3,
            'max_tokens': 2000
        }
        
        try:
            print(f"  Analyzing {token['ticker']} - {website_url}")
            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Extract JSON from response
                json_start = content.find('{')
                json_end = content.rfind('}') + 1
                if json_start >= 0 and json_end > json_start:
                    json_str = content[json_start:json_end]
                    analysis = json.loads(json_str)
                    return analysis
                else:
                    print(f"  Could not extract JSON from response")
                    return None
            else:
                print(f"  API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"  Error analyzing website: {e}")
            return None
    
    def save_analysis(self, token: Dict[str, Any], analysis: Optional[Dict[str, Any]]):
        """Save analysis results to local database"""
        if analysis:
            self.cursor.execute('''
                INSERT OR REPLACE INTO website_analysis (
                    token_id, ticker, network, contract_address, website_url,
                    website_score, website_tier, project_category,
                    has_real_utility, utility_description,
                    documentation_quality, team_transparency,
                    has_audit, has_whitepaper, has_roadmap, has_working_product,
                    red_flags, green_flags, key_findings, website_summary,
                    analysis_json, analyzed_at, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                token['id'],
                token.get('ticker', ''),
                token.get('network', ''),
                token.get('contract_address', ''),
                token.get('website_url', ''),
                analysis.get('website_score'),
                analysis.get('website_tier'),
                analysis.get('project_category'),
                analysis.get('has_real_utility'),
                analysis.get('utility_description'),
                analysis.get('documentation_quality'),
                analysis.get('team_transparency'),
                analysis.get('has_audit'),
                analysis.get('has_whitepaper'),
                analysis.get('has_roadmap'),
                analysis.get('has_working_product'),
                json.dumps(analysis.get('red_flags', [])),
                json.dumps(analysis.get('green_flags', [])),
                analysis.get('key_findings'),
                analysis.get('website_summary'),
                json.dumps(analysis),
                datetime.now().isoformat(),
                None
            ))
        else:
            # Save error record
            self.cursor.execute('''
                INSERT OR REPLACE INTO website_analysis (
                    token_id, ticker, network, contract_address, website_url,
                    analyzed_at, error_message
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                token['id'],
                token.get('ticker', ''),
                token.get('network', ''),
                token.get('contract_address', ''),
                token.get('website_url', ''),
                datetime.now().isoformat(),
                'Analysis failed'
            ))
        
        self.conn.commit()
        
    def get_stats(self):
        """Get analysis statistics"""
        self.cursor.execute('''
            SELECT 
                COUNT(*) as total,
                COUNT(CASE WHEN website_tier = 'ALPHA' THEN 1 END) as alpha,
                COUNT(CASE WHEN website_tier = 'SOLID' THEN 1 END) as solid,
                COUNT(CASE WHEN website_tier = 'BASIC' THEN 1 END) as basic,
                COUNT(CASE WHEN website_tier = 'TRASH' THEN 1 END) as trash,
                COUNT(CASE WHEN error_message IS NOT NULL THEN 1 END) as errors,
                AVG(website_score) as avg_score
            FROM website_analysis
        ''')
        
        row = self.cursor.fetchone()
        return {
            'total': row[0],
            'alpha': row[1],
            'solid': row[2],
            'basic': row[3],
            'trash': row[4],
            'errors': row[5],
            'avg_score': round(row[6], 2) if row[6] else 0
        }
    
    def run(self, batch_size=20):
        """Run the analysis process"""
        print("=" * 60)
        print("Website Analysis Script")
        print("=" * 60)
        
        # Fetch tokens
        tokens = self.fetch_tokens_to_analyze(batch_size)
        
        if not tokens:
            print("No tokens to analyze")
            return
        
        print(f"\nStarting analysis of {len(tokens)} websites...")
        print("-" * 60)
        
        for i, token in enumerate(tokens, 1):
            print(f"\n[{i}/{len(tokens)}] Processing {token['ticker']}...")
            
            # Analyze website
            analysis = self.analyze_website(token)
            
            # Save results
            self.save_analysis(token, analysis)
            
            if analysis:
                score = analysis.get('website_score', 0)
                tier = analysis.get('website_tier', 'UNKNOWN')
                print(f"  ✓ Analysis complete: Score {score}/10, Tier: {tier}")
            else:
                print(f"  ✗ Analysis failed")
            
            # Rate limiting
            if i < len(tokens):
                time.sleep(3)
        
        print("\n" + "=" * 60)
        print("Analysis Complete!")
        print("-" * 60)
        
        # Show statistics
        stats = self.get_stats()
        print(f"Total analyzed: {stats['total']}")
        print(f"  - ALPHA: {stats['alpha']}")
        print(f"  - SOLID: {stats['solid']}")
        print(f"  - BASIC: {stats['basic']}")
        print(f"  - TRASH: {stats['trash']}")
        print(f"  - Errors: {stats['errors']}")
        print(f"Average score: {stats['avg_score']}/10")
        print("=" * 60)

if __name__ == "__main__":
    analyzer = WebsiteAnalyzer()
    
    # Check for command line arguments
    batch_size = 20
    if len(sys.argv) > 1:
        try:
            batch_size = int(sys.argv[1])
        except:
            pass
    
    analyzer.run(batch_size)