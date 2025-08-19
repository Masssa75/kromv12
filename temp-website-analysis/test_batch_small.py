#!/usr/bin/env python3
"""Test with small batch"""

import os
import sys
import time
from dotenv import load_dotenv
import requests
import sqlite3
from comprehensive_website_analyzer import ComprehensiveWebsiteAnalyzer

load_dotenv()

# Database connection
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

print("🚀 TEST BATCH - 10 TOKENS")
print("="*50)

# Get 10 utility tokens with websites
print("\n📡 Fetching 10 utility tokens with websites...")

response = requests.get(
    f'{supabase_url}/rest/v1/crypto_calls',
    headers={
        'apikey': supabase_key,
        'Authorization': f'Bearer {supabase_key}'
    },
    params={
        'select': 'ticker,website_url',
        'website_url': 'not.is.null',
        'or': '(analysis_token_type.eq.utility,x_analysis_token_type.eq.utility)',
        'is_dead': 'eq.false',
        'is_invalidated': 'eq.false',
        'order': 'created_at.desc',
        'limit': '10'
    },
    timeout=30
)

if response.status_code != 200:
    print(f"Error: {response.status_code}")
    sys.exit(1)

tokens = response.json()
print(f"✅ Got {len(tokens)} tokens")

# Initialize analyzer
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, 'website_analysis_new.db')
analyzer = ComprehensiveWebsiteAnalyzer(db_path=db_path)

# Test with first token
if tokens:
    token = tokens[0]
    print(f"\n🧪 Testing with {token['ticker']}: {token['website_url']}")
    
    # Parse website
    parsed_data = analyzer.parse_website_with_playwright(token['website_url'])
    parsed_data['ticker'] = token['ticker']
    
    if parsed_data.get('success'):
        print("  ✅ Parsing succeeded")
        
        # Try AI analysis with fixed model name
        print("  🤖 Testing AI analysis...")
        ai_analyses = analyzer.analyze_with_models(parsed_data, models_to_test=[
            ("moonshotai/kimi-k2", "Kimi K2")
        ])
        
        if ai_analyses and ai_analyses[0].get('analysis'):
            score = ai_analyses[0]['analysis'].get('total_score', 0)
            print(f"  ✅ AI analysis succeeded! Score: {score}/21")
        else:
            print("  ❌ AI analysis failed")
    else:
        print(f"  ❌ Parsing failed: {parsed_data.get('error')}")

print("\n✅ Test complete!")