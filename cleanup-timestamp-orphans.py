#!/usr/bin/env python3
"""
Clean up timestamp orphans - records with price_updated_at but NULL current_price
This will make our query filtering work properly
"""
import os
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json"
}

def count_timestamp_orphans():
    """Count records with timestamps but null prices"""
    query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id&current_price.is.null&price_updated_at.not.is.null"
    resp = requests.get(query, headers={
        **headers,
        "Prefer": "count=exact"
    })
    
    if resp.status_code in [200, 206]:  # 206 = Partial Content (with count)
        count_header = resp.headers.get('Content-Range', '')
        print(f"Debug: Content-Range header: {count_header}")
        if '/' in count_header:
            count = count_header.split('/')[-1]
            return int(count) if count.isdigit() else 0
    return 0

def cleanup_orphans():
    """Clear timestamps for records with null prices"""
    update_url = f"{SUPABASE_URL}/rest/v1/crypto_calls?current_price=is.null&price_updated_at=not.is.null"
    
    update_data = {
        "price_updated_at": None,
        "price_fetched_at": None
    }
    
    resp = requests.patch(update_url, json=update_data, headers=headers)
    print(f"Debug: Cleanup response status: {resp.status_code}")
    if resp.status_code not in [200, 204]:
        print(f"Debug: Cleanup response: {resp.text}")
    return resp.status_code in [200, 204]

def main():
    print("🧹 Cleaning up timestamp orphans")
    print("=" * 50)
    
    # Count orphans before cleanup
    before_count = count_timestamp_orphans()
    print(f"📊 Found {before_count} timestamp orphans")
    
    if before_count == 0:
        print("✅ No timestamp orphans found!")
        return
    
    # Clean up
    print("🔄 Clearing orphaned timestamps...")
    if cleanup_orphans():
        print("✅ Successfully cleared orphaned timestamps")
        
        # Count after cleanup
        after_count = count_timestamp_orphans()
        cleaned = before_count - after_count
        print(f"📊 Cleaned up {cleaned} records")
        print(f"📊 Remaining orphans: {after_count}")
    else:
        print("❌ Failed to clear timestamps")

if __name__ == "__main__":
    main()