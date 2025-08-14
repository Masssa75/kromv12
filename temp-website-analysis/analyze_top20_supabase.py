#!/usr/bin/env python3
"""
Analyze top 20 tokens from Supabase database using investment scoring
"""

import os
import sys
sys.path.append('/Users/marcschwyn/Desktop/projects/KROMV12')

from dotenv import load_dotenv
from supabase import create_client
from website_investment_analyzer import WebsiteInvestmentAnalyzer
import json
import sqlite3

# Load environment variables
load_dotenv('/Users/marcschwyn/Desktop/projects/KROMV12/.env')

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not supabase_url or not supabase_key:
    print("❌ Supabase credentials not found")
    exit(1)

supabase = create_client(supabase_url, supabase_key)

# Create local database for UI
def setup_local_db():
    """Create local database for the UI"""
    conn = sqlite3.connect('analysis_results.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS website_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT UNIQUE,
            network TEXT,
            contract_address TEXT,
            website_url TEXT,
            website_score INTEGER,
            website_tier TEXT,
            website_summary TEXT,
            investment_score INTEGER,
            investment_tier TEXT,
            investment_summary TEXT,
            investment_green_flags TEXT,
            investment_red_flags TEXT,
            investment_reasoning TEXT,
            investment_analyzed_at TEXT
        )
    """)
    
    conn.commit()
    return conn

# Fetch top 20 tokens from Supabase
print("📊 Fetching top 20 tokens from Supabase...")

result = supabase.table('crypto_calls').select(
    'ticker, contract_address, network, analysis_score, analysis_tier, website_url, twitter_url, telegram_url'
).order('analysis_score', desc=True).limit(20).execute()

if not result.data:
    print("No tokens found")
    exit(1)

print(f"Found {len(result.data)} tokens")

# Setup local database
conn = setup_local_db()
cursor = conn.cursor()

# Store tokens in local database for UI
for token in result.data:
    # Extract website URL
    website_url = token.get('website_url')
    
    # Try to construct URL from ticker if not found
    if not website_url and token['ticker']:
        # Common patterns
        ticker_lower = token['ticker'].lower()
        possible_urls = [
            f"https://{ticker_lower}.com",
            f"https://{ticker_lower}.io",
            f"https://{ticker_lower}.finance",
            f"https://www.{ticker_lower}.com"
        ]
        # We'll try the first one as a guess
        website_url = possible_urls[0]
    
    # Insert or update in local database
    cursor.execute("""
        INSERT OR REPLACE INTO website_analysis 
        (ticker, network, contract_address, website_url, website_score, website_tier)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        token['ticker'],
        token['network'],
        token['contract_address'],
        website_url,
        token['analysis_score'],
        token['analysis_tier']
    ))

conn.commit()
print(f"✅ Stored {len(result.data)} tokens in local database")

# Now analyze with investment scoring
print("\n🚀 Starting investment analysis...")
analyzer = WebsiteInvestmentAnalyzer()

# Get tokens from local database
cursor.execute("""
    SELECT ticker, contract_address, website_url
    FROM website_analysis
    WHERE website_url IS NOT NULL
    ORDER BY website_score DESC NULLS LAST
    LIMIT 20
""")

tokens = cursor.fetchall()

for i, token in enumerate(tokens, 1):
    print(f"\n[{i}/{len(tokens)}] Analyzing {token[0]}...")
    
    try:
        result = analyzer.analyze_website(
            ticker=token[0],
            contract=token[1],
            url=token[2]
        )
        
        if result['success']:
            analysis = result['analysis']
            
            # Update local database with investment analysis
            cursor.execute("""
                UPDATE website_analysis
                SET investment_score = ?,
                    investment_tier = ?,
                    investment_summary = ?,
                    investment_green_flags = ?,
                    investment_red_flags = ?,
                    investment_reasoning = ?,
                    investment_analyzed_at = ?
                WHERE ticker = ?
            """, (
                analysis['investment_score'],
                analysis['tier'],
                analysis['project_summary'],
                json.dumps(analysis['green_flags']),
                json.dumps(analysis['red_flags']),
                analysis['reasoning'],
                result['analyzed_at'],
                token[0]
            ))
            
            conn.commit()
            
            print(f"  ✅ Score: {analysis['investment_score']}/10 ({analysis['tier']})")
            print(f"  📝 {analysis['project_summary'][:100]}...")
        else:
            print(f"  ❌ Error: {result['error']}")
            
    except Exception as e:
        print(f"  ❌ Exception: {e}")

conn.close()

print("\n" + "=" * 60)
print("✅ Investment analysis complete!")
print("🌐 Now start the server: python investment_server.py")
print("📊 Then visit: http://localhost:5002")