#!/usr/bin/env python3
"""Investigate why we have exactly 1000 analyzed calls"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(url, key)

print("Investigating the 1000 call limit...")
print("=" * 60)

# Check total calls vs analyzed calls
try:
    # Total calls in database
    total_result = supabase.table('crypto_calls').select('*', count='exact', head=True).execute()
    total_count = total_result.count
    print(f"Total calls in database: {total_count:,}")
    
    # Calls with Claude analysis
    claude_result = supabase.table('crypto_calls').select('*', count='exact', head=True).not_.is_('analysis_tier', 'null').execute()
    claude_count = claude_result.count
    print(f"Calls with Claude analysis: {claude_count:,}")
    
    # Calls with X analysis
    x_result = supabase.table('crypto_calls').select('*', count='exact', head=True).not_.is_('x_analysis_tier', 'null').execute()
    x_count = x_result.count
    print(f"Calls with X analysis: {x_count:,}")
    
    # Calls with notifications sent
    notified_result = supabase.table('crypto_calls').select('*', count='exact', head=True).eq('notified', True).execute()
    notified_count = notified_result.count
    print(f"Calls with notifications sent: {notified_count:,}")
    
    # Check if there's a default limit on queries
    print("\nTesting query limits...")
    
    # Try to get more than 1000 with explicit limit
    test_2000 = supabase.table('crypto_calls').select('krom_id').not_.is_('analysis_tier', 'null').limit(2000).execute()
    print(f"Query with limit(2000) returned: {len(test_2000.data)} rows")
    
    # Try with range
    test_range = supabase.table('crypto_calls').select('krom_id').not_.is_('analysis_tier', 'null').range(0, 1500).execute()
    print(f"Query with range(0, 1500) returned: {len(test_range.data)} rows")
    
    # Get the oldest and newest analyzed calls
    oldest = supabase.table('crypto_calls').select('created_at, analyzed_at').not_.is_('analysis_tier', 'null').order('created_at').limit(1).execute()
    newest = supabase.table('crypto_calls').select('created_at, analyzed_at').not_.is_('analysis_tier', 'null').order('created_at', desc=True).limit(1).execute()
    
    if oldest.data and newest.data:
        print(f"\nOldest analyzed call: {oldest.data[0]['created_at']}")
        print(f"Newest analyzed call: {newest.data[0]['created_at']}")
    
    # Check for unanalyzed calls
    unanalyzed = supabase.table('crypto_calls').select('*', count='exact', head=True).is_('analysis_tier', 'null').execute()
    print(f"\nUnanalyzed calls: {unanalyzed.count:,}")
    
except Exception as e:
    print(f"Error: {e}")