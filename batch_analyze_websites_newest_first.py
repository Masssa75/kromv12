#!/usr/bin/env python3
"""
Batch analyze websites from newest to oldest entries.
Calls the crypto-website-analyzer Edge Function for each token.
"""

import os
import time
import requests
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

# Configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
EDGE_FUNCTION_URL = f"{SUPABASE_URL}/functions/v1/crypto-website-analyzer"
DELAY_BETWEEN_CALLS = 2  # seconds between API calls

# Initialize Supabase client
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_unanalyzed_websites(limit=100):
    """Get tokens with websites that haven't been analyzed, newest first."""
    response = supabase.table('crypto_calls').select(
        'id, ticker, website_url, created_at'
    ).eq('website_analyzed', False).neq('website_url', None).order(
        'created_at', desc=True
    ).limit(limit).execute()
    
    return response.data

def analyze_website(token_data):
    """Call the Edge Function to analyze a website."""
    try:
        response = requests.post(
            EDGE_FUNCTION_URL,
            headers={
                'Authorization': f'Bearer {SUPABASE_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'url': token_data['website_url'],
                'ticker': token_data['ticker'],
                'callId': token_data['id']
            },
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                return {
                    'success': True,
                    'score': result.get('score'),
                    'tier': result.get('tier'),
                    'token_type': result.get('token_type'),
                    'database_updated': result.get('database_update', {}).get('success', False)
                }
            else:
                return {
                    'success': False,
                    'error': result.get('error', 'Unknown error')
                }
        else:
            return {
                'success': False,
                'error': f'HTTP {response.status_code}'
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

def main():
    print("=" * 70)
    print("WEBSITE ANALYSIS BATCH PROCESSOR")
    print("Analyzing from newest to oldest entries")
    print("=" * 70)
    
    # Get unanalyzed websites
    tokens = get_unanalyzed_websites(limit=100)
    total = len(tokens)
    
    if total == 0:
        print("No unanalyzed websites found!")
        return
    
    print(f"\nFound {total} tokens with unanalyzed websites")
    print(f"Processing with {DELAY_BETWEEN_CALLS}s delay between calls")
    print("-" * 70)
    
    # Statistics
    stats = {
        'success': 0,
        'failed': 0,
        'meme': 0,
        'utility': 0,
        'hybrid': 0,
        'high_tier': 0,
        'medium_tier': 0,
        'low_tier': 0
    }
    
    # Process each token
    for i, token in enumerate(tokens, 1):
        print(f"\n[{i}/{total}] {token['ticker']} - {token['website_url'][:50]}...")
        print(f"  Created: {token['created_at'][:10]}")
        
        # Analyze website
        result = analyze_website(token)
        
        if result['success']:
            stats['success'] += 1
            score = result.get('score', 0)
            tier = result.get('tier', 'LOW')
            token_type = result.get('token_type', 'unknown')
            
            print(f"  ✅ Score: {score}/21 ({tier}) - Type: {token_type.upper()}")
            
            # Update statistics
            if token_type in stats:
                stats[token_type] += 1
            if tier == 'HIGH':
                stats['high_tier'] += 1
            elif tier == 'MEDIUM':
                stats['medium_tier'] += 1
            else:
                stats['low_tier'] += 1
        else:
            stats['failed'] += 1
            print(f"  ❌ Error: {result.get('error', 'Unknown')}")
        
        # Delay between calls (except for last one)
        if i < total:
            time.sleep(DELAY_BETWEEN_CALLS)
    
    # Print summary
    print("\n" + "=" * 70)
    print("ANALYSIS COMPLETE")
    print("=" * 70)
    print(f"Total processed: {total}")
    print(f"Successful: {stats['success']} ({stats['success']/total*100:.1f}%)")
    print(f"Failed: {stats['failed']} ({stats['failed']/total*100:.1f}%)")
    print()
    print("Token Types:")
    print(f"  Meme: {stats['meme']}")
    print(f"  Utility: {stats['utility']}")
    print(f"  Hybrid: {stats['hybrid']}")
    print()
    print("Quality Tiers:")
    print(f"  HIGH (14-21): {stats['high_tier']}")
    print(f"  MEDIUM (10-13): {stats['medium_tier']}")
    print(f"  LOW (0-9): {stats['low_tier']}")
    
    # Calculate estimated time for remaining
    remaining = supabase.table('crypto_calls').select(
        'count', count='exact'
    ).eq('website_analyzed', False).neq('website_url', None).execute()
    
    if remaining.count > 0:
        estimated_time = remaining.count * (DELAY_BETWEEN_CALLS + 15) / 60
        print(f"\n📊 {remaining.count} websites still need analysis")
        print(f"⏱️  Estimated time: {estimated_time:.1f} minutes")

if __name__ == "__main__":
    main()