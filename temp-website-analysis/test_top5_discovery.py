#!/usr/bin/env python3
"""
Test analyzing top 5 token discovery websites
"""

import os
import sys
import json
import time
import sqlite3
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client
from comprehensive_website_analyzer import ComprehensiveWebsiteAnalyzer

# Load environment variables
load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(supabase_url, supabase_key)

print("=" * 80)
print("TESTING TOP 5 TOKEN WEBSITES")
print("=" * 80)

# Get tokens
response = supabase.table('token_discovery').select(
    'contract_address, symbol, network, website_url, initial_liquidity_usd'
).not_.is_('website_url', 'null').order('initial_liquidity_usd', desc=True).limit(5).execute()

tokens = response.data
print(f"\nTop 5 tokens by liquidity:")
for i, t in enumerate(tokens, 1):
    print(f"  {i}. {t['symbol']:10} ${t.get('initial_liquidity_usd', 0):>10,.0f} - {t['website_url'][:40]}")

print("\nAnalyzing with comprehensive_website_analyzer...")
analyzer = ComprehensiveWebsiteAnalyzer('token_discovery_analysis.db')

for i, token in enumerate(tokens, 1):
    print(f"\n[{i}/5] {token['symbol']}")
    print(f"  URL: {token['website_url']}")
    
    try:
        # Parse website
        print("  Parsing...")
        parsed = analyzer.parse_website_with_playwright(token['website_url'])
        
        if parsed and parsed.get('content'):
            content_len = len(str(parsed.get('content', '')))
            print(f"  ✅ Parsed {content_len} characters")
            
            # Add metadata
            parsed['ticker'] = token['symbol']
            
            # Analyze
            print("  Analyzing with AI...")
            analyses = analyzer.analyze_with_models(parsed, models_to_test=[
                ("moonshotai/kimi-k2", "Kimi K2")
            ])
            
            if analyses:
                score = analyses[0].get('total_score', 0)
                stage2 = analyses[0].get('proceed_to_stage_2', False)
                print(f"  Score: {score}/21, Stage 2: {'YES' if stage2 else 'NO'}")
            else:
                print("  ⚠️ No analysis returned")
        else:
            print("  ❌ Failed to parse")
            
    except Exception as e:
        print(f"  ❌ Error: {str(e)[:100]}")
    
    # Rate limit
    time.sleep(2)

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("To view results: python3 token_discovery_server.py")