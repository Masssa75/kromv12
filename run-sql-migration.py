#!/usr/bin/env python3
"""
Run SQL migration using Supabase client
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

print("Running enhanced analysis columns migration on Supabase...")
print("=" * 50)

# Test connection first
try:
    # Try to fetch one row to test connection
    test = supabase.table('crypto_calls').select('krom_id').limit(1).execute()
    print("✓ Connected to Supabase successfully")
except Exception as e:
    print(f"✗ Connection error: {e}")
    exit(1)

# Since we can't run raw SQL through the Python client, let's check if columns exist
# and provide instructions for manual execution
print("\nChecking existing columns...")

try:
    # Get a sample row to see existing columns
    sample = supabase.table('crypto_calls').select('*').limit(1).execute()
    
    if sample.data:
        existing_columns = list(sample.data[0].keys())
        print(f"\nExisting columns: {', '.join(existing_columns[:10])}...")
        
        # Check for new columns
        new_columns = [
            'analysis_score', 'analysis_model', 'analysis_legitimacy_factor',
            'x_analysis_score', 'x_analysis_model', 'x_best_tweet', 'x_legitimacy_factor'
        ]
        
        missing_columns = [col for col in new_columns if col not in existing_columns]
        
        if not missing_columns:
            print("\n✓ All enhanced analysis columns already exist!")
        else:
            print(f"\n⚠️  Missing columns: {', '.join(missing_columns)}")
            print("\nTo add these columns, please:")
            print("1. Go to https://supabase.com/dashboard/project/eucfoommxxvqmmwdbkdv")
            print("2. Click on 'SQL Editor' in the left sidebar")
            print("3. Copy and paste the following SQL:")
            print("\n" + "-" * 50)
            
            # Read and display SQL
            with open('add-enhanced-analysis-columns.sql', 'r') as f:
                sql_content = f.read()
                print(sql_content)
            
            print("-" * 50)
            print("\n4. Click 'Run' to execute the migration")
            print("\nAlternatively, you can use the Supabase CLI:")
            print("supabase db push --db-url postgresql://postgres.[YOUR-PROJECT-REF]:[YOUR-DB-PASSWORD]@aws-0-[YOUR-REGION].pooler.supabase.com:5432/postgres")
    
except Exception as e:
    print(f"\nError checking columns: {e}")
    print("\nPlease run the SQL migration manually in the Supabase dashboard")

print("\n✓ Migration check complete!")