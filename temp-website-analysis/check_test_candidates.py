#!/usr/bin/env python3
"""
Check for good test candidates - tokens with websites to analyze
"""

import os
import sys
sys.path.append('..')
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv('../.env')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

def get_test_candidates():
    headers = {
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
        'Content-Type': 'application/json'
    }
    
    print("=" * 80)
    print("FINDING BEST TEST CANDIDATES FOR WEBSITE ANALYSIS")
    print("=" * 80)
    
    # Query 1: High-value tokens with websites
    print("\n1. HIGH-VALUE TOKENS WITH WEBSITES (ATH ROI > 1000%):")
    print("-" * 80)
    
    query = '''
        select=ticker,network,website_url,ath_roi_percent,analysis_score,analysis_token_type
        &website_url=not.is.null
        &ath_roi_percent=gte.1000
        &is_dead=is.false
        &order=ath_roi_percent.desc
        &limit=10
    '''.replace('\n', '').replace('    ', '')
    
    response = requests.get(f"{SUPABASE_URL}/rest/v1/crypto_calls?{query}", headers=headers)
    if response.status_code == 200:
        tokens = response.json()
        for t in tokens:
            roi = f"{t['ath_roi_percent']:,.0f}%" if t['ath_roi_percent'] else "N/A"
            score = t['analysis_score'] if t['analysis_score'] else "N/A"
            print(f"  {t['ticker']:8} ({t['network']:8}) | ROI: {roi:>10} | AI Score: {score:>3} | {t['website_url'][:50]}...")
    
    # Query 2: Utility tokens with websites
    print("\n2. UTILITY TOKENS WITH WEBSITES:")
    print("-" * 80)
    
    query = '''
        select=ticker,network,website_url,ath_roi_percent,analysis_score,analysis_token_type
        &website_url=not.is.null
        &analysis_token_type=eq.utility
        &is_dead=is.false
        &order=ath_roi_percent.desc.nullsfirst
        &limit=10
    '''.replace('\n', '').replace('    ', '')
    
    response = requests.get(f"{SUPABASE_URL}/rest/v1/crypto_calls?{query}", headers=headers)
    if response.status_code == 200:
        tokens = response.json()
        for t in tokens:
            roi = f"{t['ath_roi_percent']:,.0f}%" if t['ath_roi_percent'] else "N/A"
            score = t['analysis_score'] if t['analysis_score'] else "N/A"
            print(f"  {t['ticker']:8} ({t['network']:8}) | ROI: {roi:>10} | AI Score: {score:>3} | {t['website_url'][:50]}...")
    
    # Query 3: Recent tokens with websites (last 7 days)
    print("\n3. RECENT TOKENS WITH WEBSITES (Last 7 days):")
    print("-" * 80)
    
    query = '''
        select=ticker,network,website_url,buy_timestamp,analysis_score,analysis_token_type
        &website_url=not.is.null
        &buy_timestamp=gte.2025-08-06T00:00:00Z
        &is_dead=is.false
        &order=buy_timestamp.desc
        &limit=10
    '''.replace('\n', '').replace('    ', '')
    
    response = requests.get(f"{SUPABASE_URL}/rest/v1/crypto_calls?{query}", headers=headers)
    if response.status_code == 200:
        tokens = response.json()
        for t in tokens:
            date = t['buy_timestamp'].split('T')[0] if t['buy_timestamp'] else "N/A"
            score = t['analysis_score'] if t['analysis_score'] else "N/A"
            type_str = t['analysis_token_type'] if t['analysis_token_type'] else "unknown"
            print(f"  {t['ticker']:8} ({t['network']:8}) | Date: {date} | Type: {type_str:8} | AI: {score:>3} | {t['website_url'][:40]}...")
    
    # Query 4: Mixed sample
    print("\n4. DIVERSE SAMPLE (High AI scores with websites):")
    print("-" * 80)
    
    query = '''
        select=ticker,network,website_url,analysis_score,analysis_token_type,ath_roi_percent
        &website_url=not.is.null
        &analysis_score=gte.7
        &is_dead=is.false
        &order=analysis_score.desc
        &limit=10
    '''.replace('\n', '').replace('    ', '')
    
    response = requests.get(f"{SUPABASE_URL}/rest/v1/crypto_calls?{query}", headers=headers)
    if response.status_code == 200:
        tokens = response.json()
        for t in tokens:
            score = t['analysis_score'] if t['analysis_score'] else "N/A"
            type_str = t['analysis_token_type'] if t['analysis_token_type'] else "unknown"
            roi = f"{t['ath_roi_percent']:,.0f}%" if t['ath_roi_percent'] else "N/A"
            print(f"  {t['ticker']:8} ({t['network']:8}) | AI: {score:>3} | Type: {type_str:8} | ROI: {roi:>10} | {t['website_url'][:40]}...")
    
    # Summary
    print("\n" + "=" * 80)
    print("RECOMMENDED TEST APPROACH:")
    print("-" * 80)
    print("1. Start with 5 utility tokens (most likely to have real websites)")
    print("2. Add 5 high-ROI tokens (to see if successful tokens have better sites)")
    print("3. Add 5 recent tokens (to test current project quality)")
    print("4. Add 5 high AI score tokens (to compare AI vs website quality)")
    print("\nTotal: 20 diverse tokens for comprehensive testing")
    print("=" * 80)

if __name__ == "__main__":
    get_test_candidates()