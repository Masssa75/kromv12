#!/usr/bin/env python3
import json
import urllib.request

print("=== Copying historical_price_usd to price_at_call ===")
print()

# Get service key
service_key = None
try:
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('SUPABASE_SERVICE_ROLE_KEY='):
                service_key = line.split('=', 1)[1].strip()
                break
except:
    print("❌ Could not read .env file")
    exit(1)

supabase_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/rest/v1/crypto_calls"

# Use RPC function to copy data in a single operation
print("Copying historical_price_usd to price_at_call...")

# Create the SQL query
sql_query = """
UPDATE crypto_calls 
SET price_at_call = historical_price_usd 
WHERE historical_price_usd IS NOT NULL 
AND price_at_call IS NULL;
"""

# Use Supabase Management API to execute the query
management_url = "https://api.supabase.com/v1/projects/eucfoommxxvqmmwdbkdv/database/query"

# Get management token
management_token = None
try:
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('SUPABASE_ACCESS_TOKEN='):
                management_token = line.split('=', 1)[1].strip()
                break
except:
    print("❌ Could not find SUPABASE_ACCESS_TOKEN in .env")
    exit(1)

if not management_token:
    print("❌ SUPABASE_ACCESS_TOKEN not found")
    exit(1)

# Execute the query
request_data = json.dumps({"query": sql_query})
req = urllib.request.Request(
    management_url,
    data=request_data.encode('utf-8'),
    headers={
        'Authorization': f'Bearer {management_token}',
        'Content-Type': 'application/json'
    },
    method='POST'
)

try:
    response = urllib.request.urlopen(req)
    result = response.read().decode()
    
    print("✅ Successfully copied historical_price_usd to price_at_call!")
    
    # Verify the results
    print("\nVerifying results...")
    
    # Check count of price_at_call
    count_url = f"{supabase_url}?select=count&price_at_call=not.is.null"
    req = urllib.request.Request(count_url)
    req.add_header('apikey', service_key)
    req.add_header('Authorization', f'Bearer {service_key}')
    req.add_header('Prefer', 'count=exact')
    
    response = urllib.request.urlopen(req)
    count = int(response.headers.get('content-range', '0-0/0').split('/')[-1])
    
    print(f"✅ Records with price_at_call: {count}")
    
    # Show a few examples
    example_url = f"{supabase_url}?select=ticker,historical_price_usd,price_at_call,price_source&limit=5&price_at_call=not.is.null"
    req = urllib.request.Request(example_url)
    req.add_header('apikey', service_key)
    req.add_header('Authorization', f'Bearer {service_key}')
    
    response = urllib.request.urlopen(req)
    examples = json.loads(response.read().decode())
    
    print("\nExample records:")
    for ex in examples:
        print(f"  {ex['ticker']}: historical=${ex['historical_price_usd']}, price_at_call=${ex['price_at_call']}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    
print("\n✅ Next steps:")
print("1. The krom-analysis-app should now show entry prices!")
print("2. Update crypto-poller to populate price_at_call instead of historical_price_usd")
print("3. Continue running the batch processor to populate remaining prices")