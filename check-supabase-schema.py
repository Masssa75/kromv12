#!/usr/bin/env python3
"""Check Supabase database schema and data"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(url, key)

print("Checking Supabase database schema...")
print("=" * 60)

# First, let's see what tables exist
try:
    # Get a sample row to see the structure
    sample = supabase.table('crypto_calls').select('*').limit(1).execute()
    
    if sample.data:
        print("Columns in crypto_calls table:")
        for column in sample.data[0].keys():
            print(f"  - {column}")
        
        print("\nSample data:")
        for key, value in sample.data[0].items():
            print(f"  {key}: {value}")
    
    # Get total count
    total = supabase.table('crypto_calls').select('*', count='exact').execute()
    print(f"\nTotal rows: {total.count if hasattr(total, 'count') else len(total.data)}")
    
except Exception as e:
    print(f"Error: {e}")
    
# Try to query all tables
try:
    # This query gets all tables in the public schema
    tables_query = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    """
    
    # We need to use the REST API directly for this
    import requests
    
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json"
    }
    
    # Use the SQL endpoint
    sql_url = f"{url}/rest/v1/rpc/sql"
    
    print("\n\nTrying to list all tables...")
    # This might not work if the SQL RPC is not enabled
    
except Exception as e:
    print(f"Could not list tables: {e}")