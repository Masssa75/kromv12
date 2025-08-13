#!/usr/bin/env python3
"""
Enhanced Website Verifier - Checks if website actually belongs to the token project
"""

import os
import sys
import json
import sqlite3
import requests
from datetime import datetime
from typing import Dict, Any, Optional
import re
from dotenv import load_dotenv

sys.path.append('..')
load_dotenv('../.env')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
OPEN_ROUTER_API_KEY = os.getenv('OPEN_ROUTER_API_KEY')

class WebsiteVerifier:
    def __init__(self):
        self.conn = sqlite3.connect('analysis_results.db')
        self.cursor = self.conn.cursor()
        
        # Add verification columns if they don't exist
        self.add_verification_columns()
    
    def add_verification_columns(self):
        """Add columns for verification status"""
        try:
            self.cursor.execute('''
                ALTER TABLE website_analysis 
                ADD COLUMN ca_verified BOOLEAN DEFAULT 0
            ''')
            print("Added ca_verified column")
        except:
            pass
        
        try:
            self.cursor.execute('''
                ALTER TABLE website_analysis 
                ADD COLUMN verification_method TEXT
            ''')
            print("Added verification_method column")
        except:
            pass
            
        try:
            self.cursor.execute('''
                ALTER TABLE website_analysis 
                ADD COLUMN verification_details TEXT
            ''')
            print("Added verification_details column")
        except:
            pass
            
        self.conn.commit()
    
    def verify_website_ownership(self, token: Dict[str, Any]) -> Dict[str, Any]:
        """
        Verify if the website actually belongs to the token project
        Methods:
        1. Check if contract address is mentioned on the website
        2. Check if website URL matches social links from DexScreener
        3. Use Kimi to analyze if website content matches token details
        """
        
        website_url = token.get('website_url')
        contract_address = token.get('contract_address')
        ticker = token.get('ticker')
        network = token.get('network')
        
        if not website_url or not contract_address:
            return {
                'verified': False,
                'method': 'missing_data',
                'details': 'No website URL or contract address'
            }
        
        # Create verification prompt for Kimi K2
        prompt = f"""Visit this website and verify if it belongs to this specific token project:

Website: {website_url}
Token: {ticker} on {network}
Contract Address: {contract_address}

IMPORTANT VERIFICATION TASKS:

1. CONTRACT ADDRESS CHECK:
   - Search the entire website for this exact contract address: {contract_address}
   - Check footer, header, "Buy" buttons, token info sections
   - Look for contract addresses in any format (with or without 0x prefix)
   - Note: The contract MUST match exactly, not just be "a" contract

2. TOKEN IDENTITY CHECK:
   - Does the website explicitly mention "{ticker}" token?
   - Is this the official website for THIS specific {ticker} token on {network}?
   - Or is this a general website (like apple.com) that someone linked to their token?

3. RED FLAGS TO DETECT:
   - Website is for a different project entirely (e.g., apple.com for an "APPLE" token)
   - Website is for the same-named token but on a DIFFERENT blockchain
   - Website is a general crypto tool (like DexScreener, pump.fun, etc.)
   - Website mentions a different contract address
   - Website is just a meme page with no actual token information

4. GREEN FLAGS TO CONFIRM:
   - Contract address {contract_address} is displayed on the website
   - "Buy {ticker}" button links to DEX with correct contract
   - Social links on website match our records
   - Website explicitly states it's for {ticker} on {network}

Return a JSON object:
{{
    "website_verified": <true|false>,
    "verification_method": "<contract_found|token_match|social_match|not_verified>",
    "contract_on_website": "<exact contract if found, or null>",
    "is_correct_project": <true|false>,
    "is_generic_site": <true|false>,
    "verification_confidence": <0.0-1.0>,
    "verification_details": "<explanation of verification or why it failed>",
    "red_flags_found": ["<specific issues>"],
    "green_flags_found": ["<specific confirmations>"]
}}

BE VERY STRICT: Only mark as verified if you're confident this website belongs to THIS SPECIFIC token."""

        headers = {
            'Authorization': f'Bearer {OPEN_ROUTER_API_KEY}',
            'Content-Type': 'application/json',
        }
        
        data = {
            'model': 'moonshotai/kimi-k2',
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': 0.2,  # Lower temperature for more consistent verification
            'max_tokens': 1500
        }
        
        try:
            print(f"  Verifying {ticker} - {website_url[:40]}...")
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
                    verification = json.loads(json_str)
                    
                    return {
                        'verified': verification.get('website_verified', False),
                        'method': verification.get('verification_method', 'ai_analysis'),
                        'details': verification.get('verification_details', ''),
                        'confidence': verification.get('verification_confidence', 0),
                        'contract_found': verification.get('contract_on_website'),
                        'red_flags': verification.get('red_flags_found', []),
                        'green_flags': verification.get('green_flags_found', [])
                    }
            
            return {
                'verified': False,
                'method': 'api_error',
                'details': f'API error: {response.status_code}'
            }
            
        except Exception as e:
            return {
                'verified': False,
                'method': 'error',
                'details': str(e)
            }
    
    def update_verification_status(self, token_id: str, verification: Dict[str, Any]):
        """Update database with verification results"""
        self.cursor.execute('''
            UPDATE website_analysis 
            SET ca_verified = ?,
                verification_method = ?,
                verification_details = ?
            WHERE token_id = ?
        ''', (
            1 if verification['verified'] else 0,
            verification['method'],
            json.dumps(verification),
            token_id
        ))
        self.conn.commit()
    
    def verify_high_score_tokens(self, limit=50):
        """Verify tokens with high website scores to check if they're legitimate"""
        print("=" * 80)
        print("WEBSITE OWNERSHIP VERIFICATION")
        print("=" * 80)
        
        # Get high-scoring tokens that haven't been verified
        # First check if verification column exists
        self.cursor.execute("PRAGMA table_info(website_analysis)")
        columns = [col[1] for col in self.cursor.fetchall()]
        
        if 'ca_verified' in columns:
            query = '''
                SELECT token_id, ticker, network, contract_address, website_url, website_score
                FROM website_analysis
                WHERE website_score >= 6
                AND (ca_verified IS NULL OR ca_verified = 0)
                ORDER BY website_score DESC
                LIMIT ?
            '''
        else:
            query = '''
                SELECT token_id, ticker, network, contract_address, website_url, website_score
                FROM website_analysis
                WHERE website_score >= 6
                ORDER BY website_score DESC
                LIMIT ?
            '''
        
        self.cursor.execute(query, (limit,))
        
        tokens = []
        for row in self.cursor.fetchall():
            tokens.append({
                'token_id': row[0],
                'ticker': row[1],
                'network': row[2],
                'contract_address': row[3],
                'website_url': row[4],
                'website_score': row[5]
            })
        
        print(f"\nFound {len(tokens)} high-score tokens to verify")
        print("-" * 80)
        
        verified_count = 0
        fake_count = 0
        
        for i, token in enumerate(tokens, 1):
            print(f"\n[{i}/{len(tokens)}] {token['ticker']} (Score: {token['website_score']}/10)")
            
            # Verify ownership
            verification = self.verify_website_ownership(token)
            
            # Update database
            self.update_verification_status(token['token_id'], verification)
            
            if verification['verified']:
                verified_count += 1
                print(f"  ✅ VERIFIED: {verification['method']}")
                if verification.get('contract_found'):
                    print(f"     Contract found on website!")
            else:
                fake_count += 1
                print(f"  ❌ NOT VERIFIED: {verification['details'][:100]}")
            
            # Show confidence
            confidence = verification.get('confidence', 0)
            if confidence:
                print(f"     Confidence: {confidence:.0%}")
        
        print("\n" + "=" * 80)
        print("VERIFICATION COMPLETE")
        print("-" * 80)
        print(f"✅ Verified: {verified_count} websites")
        print(f"❌ Not Verified: {fake_count} websites")
        print(f"🎯 Verification Rate: {verified_count/(verified_count+fake_count)*100:.1f}%")
        print("=" * 80)
    
    def check_specific_token(self, ticker: str):
        """Check a specific token by ticker"""
        self.cursor.execute('''
            SELECT token_id, ticker, network, contract_address, website_url, website_score
            FROM website_analysis
            WHERE ticker = ?
            LIMIT 1
        ''', (ticker,))
        
        row = self.cursor.fetchone()
        if row:
            token = {
                'token_id': row[0],
                'ticker': row[1],
                'network': row[2],
                'contract_address': row[3],
                'website_url': row[4],
                'website_score': row[5]
            }
            
            print(f"\nVerifying {token['ticker']}...")
            verification = self.verify_website_ownership(token)
            
            print("\nVerification Results:")
            print("-" * 40)
            print(f"Verified: {verification['verified']}")
            print(f"Method: {verification['method']}")
            print(f"Details: {verification['details']}")
            
            if verification.get('contract_found'):
                print(f"Contract Found: {verification['contract_found']}")
            
            if verification.get('red_flags'):
                print(f"Red Flags: {', '.join(verification['red_flags'])}")
            
            if verification.get('green_flags'):
                print(f"Green Flags: {', '.join(verification['green_flags'])}")
            
            self.update_verification_status(token['token_id'], verification)
            print("\nDatabase updated.")
        else:
            print(f"Token {ticker} not found in database")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Verify website ownership for tokens')
    parser.add_argument('--limit', type=int, default=20, help='Number of tokens to verify')
    parser.add_argument('--token', type=str, help='Verify specific token by ticker')
    
    args = parser.parse_args()
    
    verifier = WebsiteVerifier()
    
    if args.token:
        verifier.check_specific_token(args.token)
    else:
        verifier.verify_high_score_tokens(limit=args.limit)