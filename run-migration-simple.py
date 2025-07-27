#!/usr/bin/env python3
"""
Simple database migration script using Supabase Management API
"""

import os
import sys
from pathlib import Path

# Try to load dotenv, but continue if not available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Note: python-dotenv not installed, reading .env manually")
    # Manually read .env file
    env_path = Path(__file__).parent / '.env'
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

# Get Supabase credentials
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
SUPABASE_ACCESS_TOKEN = os.getenv('SUPABASE_ACCESS_TOKEN')

if not SUPABASE_URL:
    print("Error: SUPABASE_URL not found in environment")
    sys.exit(1)

# Read SQL file
sql_file = Path(__file__).parent / 'add-enhanced-analysis-columns.sql'
if not sql_file.exists():
    print(f"Error: SQL file not found at {sql_file}")
    sys.exit(1)

with open(sql_file, 'r') as f:
    sql_content = f.read()

print("=" * 60)
print("DATABASE MIGRATION FOR ENHANCED CRYPTO ANALYSIS COLUMNS")
print("=" * 60)
print()
print("This migration will add the following columns to crypto_calls table:")
print("- analysis_score (1-10 rating)")
print("- analysis_model (AI model used)")
print("- analysis_legitimacy_factor (short summary)")
print("- analysis_reanalyzed_at (timestamp)")
print("- x_analysis_score (1-10 rating for X/Twitter)")
print("- x_analysis_model (AI model used)")
print("- x_best_tweet (most informative tweet)")
print("- x_legitimacy_factor (X legitimacy summary)")
print("- x_reanalyzed_at (timestamp)")
print()
print("And create indexes for better query performance.")
print()

# Create migration instructions
print("MIGRATION OPTIONS:")
print()
print("1. Using Supabase Dashboard (Recommended):")
print("   - Go to: https://supabase.com/dashboard")
print("   - Select your project")
print("   - Navigate to SQL Editor")
print("   - Copy and paste the SQL below")
print("   - Click 'Run'")
print()
print("2. Using Supabase CLI:")
print("   supabase db push --file add-enhanced-analysis-columns.sql")
print()
print("3. Using psql directly:")
print("   psql $DATABASE_URL -f add-enhanced-analysis-columns.sql")
print()
print("=" * 60)
print("SQL TO EXECUTE:")
print("=" * 60)
print()
print(sql_content)
print()
print("=" * 60)

# Try to check if we can use requests to check the table structure
try:
    import requests
    
    # Check current table structure
    headers = {
        'apikey': SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ACCESS_TOKEN,
        'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ACCESS_TOKEN}'
    }
    
    # Try to query the table to check if it exists
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=*&limit=1"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print("\n✓ Successfully connected to Supabase")
        print("✓ crypto_calls table exists")
        
        # Check if columns already exist by looking at the response
        if response.text and response.text != '[]':
            import json
            data = json.loads(response.text)
            if data:
                existing_columns = list(data[0].keys())
                new_columns = [
                    'analysis_score', 'analysis_model', 'analysis_legitimacy_factor', 
                    'analysis_reanalyzed_at', 'x_analysis_score', 'x_analysis_model',
                    'x_best_tweet', 'x_legitimacy_factor', 'x_reanalyzed_at'
                ]
                
                already_exists = [col for col in new_columns if col in existing_columns]
                if already_exists:
                    print(f"\n⚠️  Some columns already exist: {', '.join(already_exists)}")
                    print("   The migration will skip existing columns (IF NOT EXISTS)")
                
    elif response.status_code == 404:
        print("\n⚠️  crypto_calls table not found")
        print("   You may need to create the table first")
    else:
        print(f"\n⚠️  Could not connect to Supabase (status: {response.status_code})")
        
except ImportError:
    print("\n(Note: requests library not installed, skipping connection test)")
except Exception as e:
    print(f"\n(Note: Could not test connection: {str(e)})")

print("\n" + "=" * 60)
print("Please execute the migration using one of the options above.")
print("=" * 60)