#!/usr/bin/env python3
"""
Database migration script for enhanced crypto analysis columns
Uses Supabase REST API to execute SQL commands
"""

import os
import requests
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get Supabase credentials from .env
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("Error: Missing Supabase credentials in .env file")
    print("Please ensure SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY are set")
    exit(1)

# Read SQL migration file
sql_file_path = Path(__file__).parent / 'add-enhanced-analysis-columns.sql'
if not sql_file_path.exists():
    print(f"Error: SQL file not found at {sql_file_path}")
    exit(1)

with open(sql_file_path, 'r') as f:
    sql_content = f.read()

# Split SQL content into individual statements
# Remove comments and empty lines
sql_statements = []
current_statement = []

for line in sql_content.split('\n'):
    # Skip comment lines and empty lines
    if line.strip().startswith('--') or not line.strip():
        continue
    
    current_statement.append(line)
    
    # If line ends with semicolon, it's the end of a statement
    if line.strip().endswith(';'):
        sql_statements.append(' '.join(current_statement))
        current_statement = []

# If there's a remaining statement without semicolon
if current_statement:
    sql_statements.append(' '.join(current_statement))

print(f"Found {len(sql_statements)} SQL statements to execute")

# Execute each SQL statement using Supabase REST API
headers = {
    'apikey': SUPABASE_SERVICE_ROLE_KEY,
    'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
    'Content-Type': 'application/json',
    'Prefer': 'return=minimal'
}

# Using the Supabase RPC endpoint to execute raw SQL
rpc_url = f"{SUPABASE_URL}/rest/v1/rpc"

success_count = 0
error_count = 0

for i, statement in enumerate(sql_statements, 1):
    print(f"\nExecuting statement {i}/{len(sql_statements)}:")
    print(f"{statement[:100]}..." if len(statement) > 100 else statement)
    
    # For direct SQL execution, we need to use a different approach
    # Since Supabase REST API doesn't directly support raw SQL execution,
    # we'll need to use the postgres REST API or create a function
    
    # Alternative approach: Use the Supabase client library
    try:
        # We'll use psycopg2 with the connection string derived from Supabase
        import psycopg2
        from urllib.parse import urlparse
        
        # Parse Supabase URL to get database connection details
        parsed_url = urlparse(SUPABASE_URL)
        db_host = parsed_url.hostname.replace('supabase.co', 'supabase.co')
        db_host = f"db.{parsed_url.hostname}"
        
        # Construct PostgreSQL connection string
        # Supabase uses port 5432 for direct connections
        conn_string = f"postgresql://postgres.{parsed_url.hostname.split('.')[0]}:{SUPABASE_SERVICE_ROLE_KEY}@{db_host}:5432/postgres"
        
        # Connect and execute
        conn = psycopg2.connect(conn_string)
        cur = conn.cursor()
        cur.execute(statement)
        conn.commit()
        cur.close()
        conn.close()
        
        print("✓ Success")
        success_count += 1
        
    except ImportError:
        print("\nError: psycopg2 is not installed.")
        print("Trying alternative approach with Supabase Python client...")
        
        try:
            from supabase import create_client, Client
            
            # Create Supabase client
            supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
            
            # Execute raw SQL using the Supabase client
            # Note: This requires a stored procedure or we need to use the management API
            print("Note: Direct SQL execution via Supabase Python client requires additional setup")
            print("Creating a fallback script with curl commands instead...")
            
            # Create a bash script as fallback
            with open('run-migration.sh', 'w') as f:
                f.write("#!/bin/bash\n\n")
                f.write("# Migration script using Supabase Management API\n")
                f.write("# Note: This requires Supabase CLI or direct database access\n\n")
                
                for stmt in sql_statements:
                    escaped_stmt = stmt.replace('"', '\\"').replace('\n', ' ')
                    f.write(f'echo "Executing: {escaped_stmt[:50]}..."\n')
                    f.write(f'# Add your database execution command here\n\n')
            
            os.chmod('run-migration.sh', 0o755)
            print("\nCreated run-migration.sh script")
            print("Please execute this using Supabase CLI or direct database access")
            break
            
        except ImportError:
            print("\nError: Neither psycopg2 nor supabase Python client is installed.")
            print("\nTo install required dependencies, run:")
            print("  pip install psycopg2-binary")
            print("  # or")
            print("  pip install supabase")
            
            # Create a manual migration guide
            with open('MIGRATION_GUIDE.md', 'w') as f:
                f.write("# Database Migration Guide\n\n")
                f.write("## Option 1: Using Supabase Dashboard\n\n")
                f.write("1. Go to your Supabase dashboard\n")
                f.write("2. Navigate to SQL Editor\n")
                f.write("3. Copy and paste the contents of `add-enhanced-analysis-columns.sql`\n")
                f.write("4. Click 'Run' to execute\n\n")
                f.write("## Option 2: Using Supabase CLI\n\n")
                f.write("```bash\n")
                f.write("supabase db push add-enhanced-analysis-columns.sql\n")
                f.write("```\n\n")
                f.write("## Option 3: Using psql\n\n")
                f.write("```bash\n")
                f.write("psql -h db.eucfoommxxvqmmwdbkdv.supabase.co -p 5432 -U postgres -d postgres -f add-enhanced-analysis-columns.sql\n")
                f.write("```\n\n")
                f.write("## SQL Statements to Execute:\n\n")
                f.write("```sql\n")
                f.write(sql_content)
                f.write("\n```\n")
            
            print("\nCreated MIGRATION_GUIDE.md with instructions for manual migration")
            exit(1)
    
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        error_count += 1
        
        # Continue with next statement
        continue

if success_count > 0:
    print(f"\n✅ Migration completed: {success_count} successful, {error_count} errors")
else:
    print("\n❌ Migration could not be completed automatically")
    print("Please see MIGRATION_GUIDE.md for manual migration instructions")