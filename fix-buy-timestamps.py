#!/usr/bin/env python3
"""
Fix missing buy_timestamp values by converting from raw_data.timestamp
"""

import os
from supabase import create_client, Client
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Supabase client
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(url, key)

def fix_buy_timestamps():
    print("Fixing missing buy_timestamp values...")
    
    # First, let's check how many records need fixing
    count_result = supabase.table('crypto_calls') \
        .select('id', count='exact') \
        .is_('buy_timestamp', 'null') \
        .execute()
    
    total_to_fix = count_result.count if count_result.count else 0
    print(f"Found {total_to_fix} records with NULL buy_timestamp")
    
    if total_to_fix == 0:
        print("No records to fix!")
        return
    
    # Process in batches to avoid timeouts
    batch_size = 100
    fixed_count = 0
    
    while fixed_count < total_to_fix:
        # Fetch batch of records with NULL buy_timestamp
        result = supabase.table('crypto_calls') \
            .select('id, raw_data') \
            .is_('buy_timestamp', 'null') \
            .limit(batch_size) \
            .execute()
        
        if not result.data:
            break
        
        print(f"Processing batch of {len(result.data)} records...")
        
        # Update each record
        for record in result.data:
            if record['raw_data'] and 'timestamp' in record['raw_data']:
                try:
                    # Convert Unix timestamp to datetime
                    timestamp = int(record['raw_data']['timestamp'])
                    buy_timestamp = datetime.fromtimestamp(timestamp).isoformat()
                    
                    # Update the record
                    supabase.table('crypto_calls') \
                        .update({'buy_timestamp': buy_timestamp}) \
                        .eq('id', record['id']) \
                        .execute()
                    
                    fixed_count += 1
                    
                except Exception as e:
                    print(f"Error fixing record {record['id']}: {e}")
        
        print(f"Fixed {fixed_count}/{total_to_fix} records...")
    
    print(f"✅ Successfully fixed {fixed_count} buy_timestamp values!")
    
    # Verify the fix
    verify_result = supabase.table('crypto_calls') \
        .select('id', count='exact') \
        .is_('buy_timestamp', 'null') \
        .execute()
    
    print(f"Remaining NULL buy_timestamps: {verify_result.count}")

if __name__ == "__main__":
    fix_buy_timestamps()