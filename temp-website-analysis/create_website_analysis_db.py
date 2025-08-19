#!/usr/bin/env python3
"""
Create database with all utility tokens that have websites for analysis
"""
import sqlite3
import requests
import json
from datetime import datetime

# Supabase credentials
SUPABASE_URL = "https://eucfoommxxvqmmwdbkdv.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Ria2R2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzU2Mjg4MSwiZXhwIjoyMDYzMTM4ODgxfQ.VcC7Bp3zMFYor3eVDonoG7BuS7AavemQnSOhrWcY5Y4"

def fetch_tokens_from_supabase():
    """Fetch all non-dead utility tokens with websites from Supabase"""
    headers = {
        "apikey": SUPABASE_KEY,
        "Content-Type": "application/json"
    }
    
    # Query for non-dead utility tokens WITH websites
    query_url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    
    # Need to fetch all, so we'll do it in batches
    all_tokens = []
    offset = 0
    limit = 100
    
    while True:
        params = {
            "select": "ticker,network,contract_address,website_url,liquidity_usd,twitter_url,telegram_url",
            "analysis_token_type": "eq.utility",
            "or": "(is_dead.is.null,is_dead.eq.false)",
            "website_url": "not.is.null",
            "order": "liquidity_usd.desc.nullsfirst",
            "limit": str(limit),
            "offset": str(offset)
        }
        
        response = requests.get(query_url, headers=headers, params=params)
        
        if response.status_code == 200:
            tokens = response.json()
            if not tokens:
                break
            all_tokens.extend(tokens)
            offset += limit
            print(f"Fetched {len(all_tokens)} tokens so far...")
        else:
            print(f"Error fetching from Supabase: {response.status_code}")
            break
    
    # Filter out tokens without website_url (shouldn't happen but just in case)
    tokens_with_websites = [t for t in all_tokens if t.get('website_url')]
    
    return tokens_with_websites

def create_database(tokens):
    """Create SQLite database with tokens and analysis results table"""
    
    # Connect to database
    conn = sqlite3.connect('website_analysis_new.db')
    cursor = conn.cursor()
    
    # Create tokens table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tokens (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            network TEXT NOT NULL,
            contract_address TEXT NOT NULL,
            website_url TEXT NOT NULL,
            liquidity_usd REAL,
            twitter_url TEXT,
            telegram_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create analysis results table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token_id INTEGER NOT NULL,
            ticker TEXT NOT NULL,
            website_url TEXT NOT NULL,
            score INTEGER,
            tier TEXT,
            legitimacy_indicators TEXT,
            red_flags TEXT,
            technical_depth TEXT,
            team_transparency TEXT,
            reasoning TEXT,
            raw_response TEXT,
            analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (token_id) REFERENCES tokens (id)
        )
    ''')
    
    # Insert tokens
    for token in tokens:
        cursor.execute('''
            INSERT INTO tokens (ticker, network, contract_address, website_url, liquidity_usd, twitter_url, telegram_url)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            token['ticker'],
            token['network'],
            token['contract_address'],
            token['website_url'],
            token.get('liquidity_usd'),
            token.get('twitter_url'),
            token.get('telegram_url')
        ))
    
    conn.commit()
    conn.close()
    
    print(f"Database created with {len(tokens)} tokens")

def main():
    print("Fetching utility tokens with websites from Supabase...")
    tokens = fetch_tokens_from_supabase()
    print(f"Found {len(tokens)} tokens with websites")
    
    print("\nCreating database...")
    create_database(tokens)
    
    # Show top 10 by liquidity
    print("\nTop 10 tokens by liquidity:")
    tokens_with_liq = [t for t in tokens if t.get('liquidity_usd')]
    tokens_with_liq.sort(key=lambda x: x['liquidity_usd'], reverse=True)
    
    for i, token in enumerate(tokens_with_liq[:10], 1):
        print(f"{i}. {token['ticker']:<10} ${token['liquidity_usd']:>15,.0f}  {token['website_url']}")

if __name__ == "__main__":
    main()