#!/usr/bin/env python3
"""
Clean up ALL database records by clearing timestamps for records with null prices.
This loops until all records are cleaned.
"""

import os
import requests
import time
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json"
}

total_cleaned = 0

while True:
    # Check how many records need cleaning
    check_query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id&current_price.is.null&price_updated_at.not.is.null&limit=1000"
    response = requests.get(check_query, headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Error checking records: {response.status_code}")
        break
    
    records = response.json()
    
    if not records:
        print(f"\n✅ All done! Total cleaned: {total_cleaned} records")
        break
    
    print(f"\n📊 Found {len(records)} records to clean...")
    
    # Get the IDs
    record_ids = [r['id'] for r in records]
    
    # Update in batches of 100
    batch_size = 100
    batch_cleaned = 0
    
    for i in range(0, len(record_ids), batch_size):
        batch_ids = record_ids[i:i+batch_size]
        
        # Update this batch
        update_response = requests.patch(
            f"{SUPABASE_URL}/rest/v1/crypto_calls?id=in.({','.join(batch_ids)})",
            headers=headers,
            json={
                "price_updated_at": None,
                "price_fetched_at": None
            }
        )
        
        if update_response.status_code == 204:
            batch_cleaned += len(batch_ids)
            print(f"  ✅ Cleaned batch: {len(batch_ids)} records")
        else:
            print(f"  ❌ Failed to update batch: {update_response.status_code}")
        
        # Small delay to avoid rate limits
        time.sleep(0.1)
    
    total_cleaned += batch_cleaned
    print(f"📊 Running total: {total_cleaned} records cleaned")
    
    # Brief pause before next iteration
    time.sleep(1)

# Final verification
verify_query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id&current_price.is.null&price_updated_at.not.is.null&limit=1"
verify_response = requests.get(verify_query, headers=headers)

if verify_response.status_code == 200 and len(verify_response.json()) == 0:
    print("\n✅ Verification passed - database is completely clean!")
else:
    print("\n⚠️  Some records may still have issues")