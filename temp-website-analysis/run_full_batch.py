#!/usr/bin/env python3
"""Run full batch analysis - simplified version"""

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

print("\n" + "="*80)
print("🚀 FULL BATCH WEBSITE ANALYSIS - STARTING")
print("="*80)

# Get utility tokens with websites from Supabase
print("\n📡 Fetching UTILITY tokens (non-dead) with websites from Supabase...")

try:
    response = requests.get(
        f'{supabase_url}/rest/v1/crypto_calls',
        headers={
            'apikey': supabase_key,
            'Authorization': f'Bearer {supabase_key}'
        },
        params={
            'select': 'ticker,website_url',
            'website_url': 'not.is.null',
            'analysis_token_type': 'eq.utility',
            'order': 'created_at.desc',
            'limit': '400'
        },
        timeout=30
    )
    
    if response.status_code != 200:
        print(f"Error: {response.status_code} - {response.text[:200]}")
        sys.exit(1)
    
    tokens = response.json()
    print(f"✅ Found {len(tokens)} tokens with websites")
    
except Exception as e:
    print(f"❌ Error fetching from Supabase: {e}")
    sys.exit(1)

# Get already analyzed
print("\n📊 Checking already analyzed...")
# Get the directory where this script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(script_dir, 'website_analysis_new.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()
cursor.execute("SELECT DISTINCT url FROM website_analysis WHERE total_score > 0")
analyzed = set(row[0] for row in cursor.fetchall())
conn.close()
print(f"✅ Already analyzed: {len(analyzed)} websites")

# Filter to analyze
to_analyze = []
seen_urls = set()
for token in tokens:
    url = token['website_url']
    if url not in analyzed and url not in seen_urls:
        to_analyze.append((token['ticker'], url))
        seen_urls.add(url)

print(f"\n📋 To analyze: {len(to_analyze)} new websites")
print(f"💰 Estimated cost: ${len(to_analyze) * 0.003:.2f} (Kimi K2)")
print(f"⏱️  Estimated time: {len(to_analyze) * 15 / 60:.1f} minutes")

if not to_analyze:
    print("\n✅ All tokens already analyzed!")
    sys.exit(0)

# Confirm
print("\n" + "="*80)
print("Starting analysis in 3 seconds... (Ctrl+C to cancel)")
print("="*80)
time.sleep(3)

# Analyze
analyzer = ComprehensiveWebsiteAnalyzer(db_path=db_path)
start_time = time.time()

for i, (ticker, url) in enumerate(to_analyze):
    print(f"\n[{i+1}/{len(to_analyze)}] Analyzing {ticker}: {url}")
    
    try:
        # Parse
        print("  📄 Parsing website...")
        parsed_data = analyzer.parse_website_with_playwright(url)
        parsed_data['ticker'] = ticker
        
        if parsed_data.get('success'):
            # Analyze with Kimi K2 only for speed
            print("  🤖 Analyzing with AI...")
            ai_analyses = analyzer.analyze_with_models(parsed_data, models_to_test=[
                ("moonshotai/kimi-k2", "Kimi K2")
            ])
            
            if ai_analyses and ai_analyses[0].get('analysis'):
                score = ai_analyses[0]['analysis'].get('total_score', 0)
                print(f"  ✅ Score: {score}/21")
                
                # Save
                analyzer.save_to_database(url, parsed_data, ai_analyses)
                print("  💾 Saved to database")
            else:
                print("  ⚠️ AI analysis failed")
        else:
            print(f"  ❌ Parsing failed: {parsed_data.get('error')}")
    
    except Exception as e:
        print(f"  ❌ Error: {e}")
    
    # Progress update
    if (i + 1) % 10 == 0:
        elapsed = time.time() - start_time
        rate = (i + 1) / elapsed
        remaining = (len(to_analyze) - i - 1) / rate / 60
        print(f"\n📊 Progress: {i+1}/{len(to_analyze)} ({(i+1)/len(to_analyze)*100:.1f}%)")
        print(f"⏱️  Time remaining: {remaining:.1f} minutes")

# Complete
elapsed = time.time() - start_time
print("\n" + "="*80)
print(f"✅ BATCH COMPLETE!")
print(f"📊 Analyzed: {len(to_analyze)} websites")
print(f"⏱️  Total time: {elapsed/60:.1f} minutes")
print(f"💰 Total cost: ${len(to_analyze) * 0.003:.2f}")
print("="*80)
print("\n🌐 View results at: http://localhost:5006")