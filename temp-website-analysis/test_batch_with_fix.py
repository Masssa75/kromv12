#!/usr/bin/env python3
"""Test batch with proper database saving"""
import sqlite3
import json
import time
from datetime import datetime
from comprehensive_website_analyzer import ComprehensiveWebsiteAnalyzer

def manually_save_result(url, parsed_data, analysis_result):
    """Manually save to database if the analyzer fails to"""
    conn = sqlite3.connect('website_analysis_new.db')
    cursor = conn.cursor()
    
    # Ensure table exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS website_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT,
            url TEXT,
            parsed_content TEXT,
            documents_found INTEGER,
            team_members_found INTEGER,
            linkedin_profiles INTEGER,
            website_description TEXT,
            score REAL,
            tier TEXT,
            legitimacy_indicators TEXT,
            red_flags TEXT,
            technical_depth TEXT,
            team_transparency TEXT,
            reasoning TEXT,
            analyzed_at TIMESTAMP,
            parse_success BOOLEAN,
            parse_error TEXT
        )
    """)
    
    # Prepare data
    score = analysis_result.get('score', 0) if analysis_result else 0
    team_count = analysis_result.get('team_members_count', 0) if analysis_result else 0
    reasoning = analysis_result.get('reasoning', '') if analysis_result else ''
    
    # Insert record
    cursor.execute("""
        INSERT INTO website_analysis 
        (url, parsed_content, documents_found, team_members_found, 
         linkedin_profiles, score, tier, reasoning, 
         analyzed_at, parse_success, parse_error)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        url,
        json.dumps(parsed_data) if parsed_data else '{}',
        len(parsed_data.get('documents', [])) if parsed_data else 0,
        team_count,
        len(parsed_data.get('team_data', {}).get('linkedin_profiles', [])) if parsed_data else 0,
        score,
        'HIGH' if score >= 7 else 'MEDIUM' if score >= 4 else 'LOW',
        reasoning,
        datetime.now().isoformat(),
        parsed_data.get('success', False) if parsed_data else False,
        parsed_data.get('error', '') if parsed_data else ''
    ))
    
    conn.commit()
    conn.close()
    print(f"  💾 Manually saved to database")

# Test URLs - top utility tokens from Supabase
test_urls = [
    ('STRAT', 'https://www.ethstrat.xyz/'),
    ('REX', 'https://www.etherex.finance/'),
    ('MAMO', 'https://mamo.bot/'),
    ('NKP', 'https://nonkyotoprotocol.com/'),
    ('COLLAT', 'https://www.collaterize.com/'),
    ('GRAY', 'https://www.gradient.trade/'),
    ('QBIT', 'https://qbit.technology/'),
    ('MSIA', 'https://messiah.network'),
    ('VIBE', 'https://jup.ag/studio/DFVeSFxNohR5CVuReaXSz6rGuJ62GE53ZTaWCJzj69DG')
]

print("Starting test batch with database fix...")
print("="*60)

analyzer = ComprehensiveWebsiteAnalyzer()
models = [("moonshotai/kimi-k2", "Kimi K2")]

success_count = 0
fail_count = 0

for ticker, url in test_urls:
    print(f"\n[{ticker}] {url}")
    
    try:
        # Parse website
        parsed = analyzer.parse_website_with_playwright(url)
        
        if parsed['success']:
            # Analyze with Kimi K2
            results = analyzer.analyze_with_models(parsed, models_to_test=models)
            
            # Check if it was saved
            conn = sqlite3.connect('website_analysis_new.db')
            cursor = conn.cursor()
            cursor.execute("SELECT score FROM website_analysis WHERE url = ? ORDER BY analyzed_at DESC LIMIT 1", (url,))
            saved = cursor.fetchone()
            conn.close()
            
            if saved:
                success_count += 1
                print(f"  ✅ Saved successfully: Score {saved[0]}/10")
            else:
                # Manually save if not saved
                if results and len(results) > 0:
                    manually_save_result(url, parsed, results[0])
                    success_count += 1
                else:
                    print(f"  ⚠️ No analysis results")
                    fail_count += 1
        else:
            fail_count += 1
            print(f"  ❌ Parse failed: {parsed.get('error', 'Unknown')[:50]}")
            
    except Exception as e:
        fail_count += 1
        print(f"  ❌ Error: {str(e)[:100]}")
    
    time.sleep(2)

# Final check
conn = sqlite3.connect('website_analysis_new.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(DISTINCT url) FROM website_analysis")
total_count = cursor.fetchone()[0]

# Get all unique URLs
cursor.execute("SELECT DISTINCT url, score FROM website_analysis ORDER BY score DESC")
all_urls = cursor.fetchall()
conn.close()

print(f"\n{'='*60}")
print(f"TEST BATCH COMPLETE")
print(f"{'='*60}")
print(f"✅ Successful: {success_count}")
print(f"❌ Failed: {fail_count}")
print(f"📊 Total unique URLs in database: {total_count}")

print(f"\n🌐 All analyzed websites ({len(all_urls)}):")
for url, score in all_urls:
    tier = "🟢" if score >= 7 else "🟡" if score >= 4 else "🔴"
    print(f"  {tier} {score:.1f}/10: {url[:60]}...")

print(f"\n📊 View results at http://localhost:5005")