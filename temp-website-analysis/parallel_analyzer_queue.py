#!/usr/bin/env python3
"""
Parallel Website Analyzer with Queue-based Architecture
- Multiple workers for Kimi K2 API calls (parallel)
- Single writer for SQLite (sequential)
- No database lock issues!
"""

import os
import sys
import json
import sqlite3
import time
from datetime import datetime
from typing import Dict, Any, Optional
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import threading
from dotenv import load_dotenv

# Load environment variables
sys.path.append('..')
load_dotenv('../.env')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
OPEN_ROUTER_API_KEY = os.getenv('OPEN_ROUTER_API_KEY')

class ParallelWebsiteAnalyzer:
    def __init__(self, num_workers=10):
        self.num_workers = num_workers
        self.results_queue = Queue()
        self.stats = {
            'total': 0,
            'completed': 0,
            'failed': 0,
            'start_time': None,
            'tokens_per_minute': 0
        }
        self.init_database()
        
    def init_database(self):
        """Initialize local SQLite database"""
        self.conn = sqlite3.connect('analysis_results.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        # Create table with website_summary
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
        self.conn.commit()
    
    def fetch_tokens_to_analyze(self, limit=100, token_type='utility'):
        """Fetch tokens from Supabase"""
        headers = {
            'apikey': SUPABASE_SERVICE_ROLE_KEY,
            'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
            'Content-Type': 'application/json'
        }
        
        # Build query based on token type
        if token_type == 'utility':
            type_filter = '&analysis_token_type=eq.utility'
        elif token_type == 'high_value':
            type_filter = '&ath_roi_percent=gte.1000'
        else:
            type_filter = ''
        
        query = f'''
            select=id,ticker,contract_address,network,website_url,analysis_token_type,ath_roi_percent
            &website_url=not.is.null
            &website_analyzed_at=is.null
            &is_dead=is.false
            &is_invalidated=is.false
            {type_filter}
            &order=ath_roi_percent.desc.nullsfirst
            &limit={limit}
        '''.replace('\n', '').replace('    ', '')
        
        url = f"{SUPABASE_URL}/rest/v1/crypto_calls?{query}"
        
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                tokens = response.json()
                
                # Filter out already analyzed tokens
                self.cursor.execute("SELECT token_id FROM website_analysis")
                analyzed_ids = set(row[0] for row in self.cursor.fetchall())
                new_tokens = [t for t in tokens if t['id'] not in analyzed_ids]
                
                return new_tokens
            else:
                print(f"Error fetching from Supabase: {response.status_code}")
                return []
        except Exception as e:
            print(f"Error fetching tokens: {e}")
            return []
    
    def analyze_website_worker(self, token: Dict[str, Any]) -> Dict[str, Any]:
        """Worker function to analyze a single website (runs in parallel)"""
        website_url = token.get('website_url')
        if not website_url:
            return {'token': token, 'analysis': None, 'error': 'No website URL'}
        
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
}}"""

        headers = {
            'Authorization': f'Bearer {OPEN_ROUTER_API_KEY}',
            'Content-Type': 'application/json',
        }
        
        data = {
            'model': 'moonshotai/kimi-k2',
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.3,
            'max_tokens': 2000
        }
        
        try:
            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers=headers,
                json=data,
                timeout=45
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
                    return {'token': token, 'analysis': analysis, 'error': None}
            
            return {'token': token, 'analysis': None, 'error': f'API error: {response.status_code}'}
                
        except Exception as e:
            return {'token': token, 'analysis': None, 'error': str(e)}
    
    def database_writer(self):
        """Single thread that writes all results to database"""
        while True:
            result = self.results_queue.get()
            
            if result is None:  # Shutdown signal
                break
                
            token = result['token']
            analysis = result['analysis']
            error = result['error']
            
            try:
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
                    self.stats['completed'] += 1
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
                        error or 'Analysis failed'
                    ))
                    self.stats['failed'] += 1
                
                self.conn.commit()
                
                # Update progress
                elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
                total_processed = self.stats['completed'] + self.stats['failed']
                self.stats['tokens_per_minute'] = (total_processed / elapsed) * 60 if elapsed > 0 else 0
                
                # Print progress
                print(f"[{total_processed}/{self.stats['total']}] {token.get('ticker', 'Unknown'):8} - "
                      f"{'✓' if analysis else '✗'} "
                      f"{analysis.get('website_tier', 'ERROR') if analysis else error[:30]}"
                      f" | Speed: {self.stats['tokens_per_minute']:.1f} tokens/min")
                
            except Exception as e:
                print(f"Database error for {token.get('ticker')}: {e}")
            
            self.results_queue.task_done()
    
    def run(self, limit=100, token_type='utility'):
        """Main execution function"""
        print("=" * 80)
        print(f"PARALLEL WEBSITE ANALYZER - {self.num_workers} Workers")
        print("=" * 80)
        
        # Fetch tokens
        tokens = self.fetch_tokens_to_analyze(limit, token_type)
        
        if not tokens:
            print("No tokens to analyze")
            return
        
        self.stats['total'] = len(tokens)
        self.stats['start_time'] = datetime.now()
        
        print(f"\nAnalyzing {len(tokens)} websites with {self.num_workers} parallel workers...")
        print(f"Architecture: {self.num_workers} API workers → Queue → 1 Database writer")
        print("-" * 80)
        
        # Start database writer thread
        writer_thread = threading.Thread(target=self.database_writer)
        writer_thread.start()
        
        # Process tokens in parallel
        with ThreadPoolExecutor(max_workers=self.num_workers) as executor:
            # Submit all tasks
            futures = [executor.submit(self.analyze_website_worker, token) for token in tokens]
            
            # Process results as they complete
            for future in as_completed(futures):
                try:
                    result = future.result(timeout=60)
                    self.results_queue.put(result)
                except Exception as e:
                    print(f"Worker error: {e}")
        
        # Wait for queue to be processed
        self.results_queue.join()
        
        # Shutdown writer thread
        self.results_queue.put(None)
        writer_thread.join()
        
        # Final statistics
        elapsed = (datetime.now() - self.stats['start_time']).total_seconds()
        print("\n" + "=" * 80)
        print("ANALYSIS COMPLETE!")
        print("-" * 80)
        print(f"Total processed: {self.stats['completed'] + self.stats['failed']}")
        print(f"  ✓ Successful: {self.stats['completed']}")
        print(f"  ✗ Failed: {self.stats['failed']}")
        print(f"Time elapsed: {elapsed/60:.1f} minutes")
        print(f"Average speed: {self.stats['tokens_per_minute']:.1f} tokens/minute")
        print(f"Cost estimate: ${(self.stats['completed'] + self.stats['failed']) * 0.00008:.2f}")
        print("=" * 80)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Parallel Website Analyzer')
    parser.add_argument('--workers', type=int, default=10, help='Number of parallel workers (default: 10)')
    parser.add_argument('--limit', type=int, default=50, help='Number of tokens to analyze (default: 50)')
    parser.add_argument('--type', choices=['utility', 'high_value', 'all'], default='utility', 
                       help='Type of tokens to analyze (default: utility)')
    
    args = parser.parse_args()
    
    analyzer = ParallelWebsiteAnalyzer(num_workers=args.workers)
    analyzer.run(limit=args.limit, token_type=args.type)