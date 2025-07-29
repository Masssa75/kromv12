#!/usr/bin/env python3
"""
Clean up database by clearing timestamps for records with null prices.
This fixes the issue where clear-prices wasn't clearing timestamps.
"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json"
}

# First, check how many records have this issue
check_query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id&current_price.is.null&price_updated_at.not.is.null"
response = requests.get(check_query, headers={**headers, "Prefer": "count=exact"})

if 'content-range' in response.headers:
    total_affected = response.headers['content-range'].split('/')[-1]
    print(f"📊 Found {total_affected} records with null prices but non-null timestamps")
else:
    print("❌ Could not get count of affected records")
    exit(1)

if int(total_affected) == 0:
    print("✅ No cleanup needed - database is already clean!")
    exit(0)

# Auto-confirm for non-interactive mode
print(f"\n🔄 Proceeding to clean up {total_affected} records...")

# Perform the cleanup
print(f"\n🧹 Cleaning up {total_affected} records...")

cleanup_data = {
    "price_updated_at": None,
    "price_fetched_at": None
}

# Need to get the IDs first since we can't do complex updates directly
get_ids_query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id&current_price.is.null&price_updated_at.not.is.null&limit=10000"
response = requests.get(get_ids_query, headers=headers)

if response.status_code != 200:
    print(f"❌ Error getting record IDs: {response.status_code}")
    exit(1)

records = response.json()
record_ids = [r['id'] for r in records]

if not record_ids:
    print("✅ No records to clean up")
    exit(0)

# Update in batches of 100
batch_size = 100
total_updated = 0

for i in range(0, len(record_ids), batch_size):
    batch_ids = record_ids[i:i+batch_size]
    
    # Update this batch
    update_response = requests.patch(
        f"{SUPABASE_URL}/rest/v1/crypto_calls?id=in.({','.join(batch_ids)})",
        headers=headers,
        json=cleanup_data
    )
    
    if update_response.status_code == 204:
        total_updated += len(batch_ids)
        print(f"  ✅ Updated batch {i//batch_size + 1}: {len(batch_ids)} records")
    else:
        print(f"  ❌ Failed to update batch: {update_response.status_code}")
        print(f"     Response: {update_response.text}")

print(f"\n✅ Cleanup complete! Updated {total_updated} records")

# Verify the cleanup
verify_query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id&current_price.is.null&price_updated_at.not.is.null&limit=1"
verify_response = requests.get(verify_query, headers=headers)

if verify_response.status_code == 200 and len(verify_response.json()) == 0:
    print("✅ Verification passed - no more records with mismatched null prices and timestamps")
else:
    print("⚠️  Some records may still have issues")