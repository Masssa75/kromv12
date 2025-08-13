#!/usr/bin/env python3
"""
Calculate analysis metrics and time estimates
"""

import os
import sys
sys.path.append('..')
from dotenv import load_dotenv
import requests
import sqlite3
from datetime import datetime

# Load environment variables
load_dotenv('../.env')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

def get_utility_token_counts():
    headers = {
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
        'Content-Type': 'application/json'
    }
    
    print("=" * 80)
    print("WEBSITE ANALYSIS METRICS & TIME ESTIMATES")
    print("=" * 80)
    
    # Count utility tokens with websites
    query = '''
        select=count
        &website_url=not.is.null
        &analysis_token_type=eq.utility
        &is_dead=is.false
        &is_invalidated=is.false
    '''.replace('\n', '').replace('    ', '')
    
    response = requests.get(f"{SUPABASE_URL}/rest/v1/crypto_calls?{query}", headers=headers)
    utility_with_websites = 0
    if response.status_code == 200:
        result = response.json()
        if result and isinstance(result, list) and len(result) > 0:
            utility_with_websites = result[0].get('count', 0)
    
    # Count all non-dead tokens with websites
    query2 = '''
        select=count
        &website_url=not.is.null
        &is_dead=is.false
        &is_invalidated=is.false
    '''.replace('\n', '').replace('    ', '')
    
    response2 = requests.get(f"{SUPABASE_URL}/rest/v1/crypto_calls?{query2}", headers=headers)
    total_with_websites = 0
    if response2.status_code == 200:
        result2 = response2.json()
        if result2 and isinstance(result2, list) and len(result2) > 0:
            total_with_websites = result2[0].get('count', 0)
    
    # Check local analysis timing
    conn = sqlite3.connect('analysis_results.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            COUNT(*) as analyzed,
            MIN(analyzed_at) as first_analysis,
            MAX(analyzed_at) as last_analysis
        FROM website_analysis
        WHERE analyzed_at IS NOT NULL
    ''')
    
    row = cursor.fetchone()
    analyzed_count = row[0] if row else 0
    
    # Calculate timing
    if row and row[1] and row[2] and analyzed_count > 0:
        first_time = datetime.fromisoformat(row[1])
        last_time = datetime.fromisoformat(row[2])
        duration = (last_time - first_time).total_seconds()
        avg_time_per_token = duration / analyzed_count if analyzed_count > 0 else 0
    else:
        avg_time_per_token = 10  # Default estimate
    
    conn.close()
    
    print("\n📊 TOKEN COUNTS:")
    print("-" * 80)
    print(f"Utility tokens with websites (non-dead): {utility_with_websites}")
    print(f"All tokens with websites (non-dead): {total_with_websites}")
    
    print("\n⏱️ ANALYSIS SPEED:")
    print("-" * 80)
    print(f"Tokens analyzed in this session: {analyzed_count}")
    if analyzed_count > 0:
        print(f"Average time per token: {avg_time_per_token:.1f} seconds")
        print(f"Tokens per hour: {3600/avg_time_per_token:.0f}")
    else:
        print(f"Estimated time per token: ~10 seconds (7s API + 3s delay)")
        print(f"Estimated tokens per hour: ~360")
    
    print("\n📈 TIME ESTIMATES FOR UTILITY TOKENS:")
    print("-" * 80)
    
    # Calculate estimates
    seconds_per_token = avg_time_per_token if analyzed_count > 0 else 10
    
    if utility_with_websites > 0:
        total_seconds = utility_with_websites * seconds_per_token
        hours = total_seconds / 3600
        
        print(f"Total utility tokens to analyze: {utility_with_websites}")
        print(f"Time per token: {seconds_per_token:.1f} seconds")
        print(f"Total time needed: {hours:.1f} hours ({hours/24:.1f} days)")
        
        # With parallel processing
        print("\n🚀 WITH OPTIMIZATIONS:")
        print("-" * 80)
        print(f"If we run 2 parallel processes: {hours/2:.1f} hours")
        print(f"If we run 3 parallel processes: {hours/3:.1f} hours")
        print(f"If we run 5 parallel processes: {hours/5:.1f} hours")
        
        # Batch processing estimates
        print("\n📦 BATCH PROCESSING:")
        print("-" * 80)
        print(f"Processing 50 tokens takes: {50*seconds_per_token/60:.1f} minutes")
        print(f"Processing 100 tokens takes: {100*seconds_per_token/60:.1f} minutes")
        print(f"Processing 500 tokens takes: {500*seconds_per_token/3600:.1f} hours")
    
    print("\n💰 COST ESTIMATES (Kimi K2 via OpenRouter):")
    print("-" * 80)
    cost_per_1000 = 0.08  # $0.08 per 1000 analyses
    cost_per_token = cost_per_1000 / 1000
    
    if utility_with_websites > 0:
        total_cost = utility_with_websites * cost_per_token
        print(f"Cost per analysis: ${cost_per_token:.5f}")
        print(f"Total cost for {utility_with_websites} utility tokens: ${total_cost:.2f}")
        print(f"Total cost for {total_with_websites} all tokens: ${total_with_websites * cost_per_token:.2f}")
    
    print("\n✅ RECOMMENDATIONS:")
    print("-" * 80)
    print("1. Start with high-value utility tokens (ATH ROI > 100%)")
    print("2. Run overnight batch of 500-1000 tokens")
    print("3. Use 2-3 parallel processes for faster completion")
    print("4. Total utility tokens can be done in 1-2 days")
    print("5. Very low cost - under $5 for all tokens")
    
    print("=" * 80)

if __name__ == "__main__":
    get_utility_token_counts()