#!/usr/bin/env python3
import json
import urllib.request

print("=== Deleting Recent DEAD_TOKEN Records for Re-fetch ===")
print()

supabase_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/rest/v1/crypto_calls"
service_key = None

# Read the service key from .env
try:
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('SUPABASE_SERVICE_ROLE_KEY='):
                service_key = line.split('=', 1)[1].strip()
                break
except:
    print("❌ Could not read .env file")
    exit(1)

# Get recent calls with DEAD_TOKEN that we know should work
query_url = f"{supabase_url}?select=krom_id,ticker,pool_address&price_source=eq.DEAD_TOKEN&network=eq.ethereum&ticker=in.($OPTI,HONOKA)&order=created_at.desc"
print(f"Finding recent DEAD_TOKEN records for $OPTI and HONOKA...")

req = urllib.request.Request(query_url)
req.add_header('apikey', service_key)
req.add_header('Authorization', f'Bearer {service_key}')

try:
    response = urllib.request.urlopen(req)
    calls = json.loads(response.read().decode())
    
    print(f"Found {len(calls)} DEAD_TOKEN records to delete:")
    
    for call in calls:
        print(f"  {call['ticker']} - {call['krom_id']}")
    
    if len(calls) > 0:
        print()
        confirm = input(f"Delete these {len(calls)} records so they can be re-fetched? (y/N): ")
        
        if confirm.lower() == 'y':
            # Delete these records
            krom_ids = [call['krom_id'] for call in calls]
            
            for krom_id in krom_ids:
                delete_url = f"{supabase_url}?krom_id=eq.{krom_id}"
                
                delete_req = urllib.request.Request(delete_url, method='DELETE')
                delete_req.add_header('apikey', service_key)
                delete_req.add_header('Authorization', f'Bearer {service_key}')
                
                try:
                    delete_response = urllib.request.urlopen(delete_req)
                    print(f"✅ Deleted {krom_id}")
                except Exception as e:
                    print(f"❌ Failed to delete {krom_id}: {e}")
            
            print()
            print("🎯 Records deleted! Now test the crypto-poller again.")
            print("The same calls should be re-fetched with correct prices.")
        else:
            print("Cancelled - no records deleted")
    else:
        print("No records found to delete")
        
except Exception as e:
    print(f"❌ Error: {e}")