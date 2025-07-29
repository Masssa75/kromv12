#!/usr/bin/env python3
import json
import urllib.request
from datetime import datetime

# Get service key
service_key = None
with open('.env', 'r') as f:
    for line in f:
        if line.startswith('SUPABASE_SERVICE_ROLE_KEY='):
            service_key = line.split('=', 1)[1].strip()
            break

supabase_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/rest/v1/crypto_calls"
edge_function_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-historical"

# Get a few unprocessed tokens to test
url = f"{supabase_url}?select=*&price_at_call=is.null&price_source=is.null&limit=5"
req = urllib.request.Request(url)
req.add_header('apikey', service_key)
req.add_header('Authorization', f'Bearer {service_key}')

response = urllib.request.urlopen(req)
test_tokens = json.loads(response.read().decode())

print(f"=== Testing {len(test_tokens)} Unprocessed Tokens ===\n")

for i, token in enumerate(test_tokens):
    print(f"\n{i+1}. Testing {token['ticker']} ({token['network']})")
    print(f"   Contract: {token['contract_address']}")
    print(f"   Pool: {token['pool_address']}")
    print(f"   Created: {token['created_at']}")
    
    # Check KROM price first
    krom_price = token.get('raw_data', {}).get('trade', {}).get('buyPrice')
    if krom_price:
        print(f"   ✅ Has KROM price: ${krom_price}")
        continue
    
    # Try to fetch from GeckoTerminal
    timestamp_str = token['created_at']
    
    # Parse timestamp
    try:
        if 'Z' in timestamp_str:
            timestamp_str = timestamp_str.replace('Z', '+00:00')
        if '.' in timestamp_str and '+' in timestamp_str:
            parts = timestamp_str.split('.')
            microsec, tz = parts[1].split('+')
            microsec = microsec.ljust(6, '0')[:6]
            timestamp_str = f"{parts[0]}.{microsec}+{tz}"
        
        unix_timestamp = int(datetime.fromisoformat(timestamp_str).timestamp())
    except Exception as e:
        print(f"   ❌ Failed to parse timestamp: {e}")
        continue
    
    # Map network
    network = token['network']
    if network.lower() == 'ethereum':
        network = 'eth'
    
    # Call edge function
    request_data = {
        "contractAddress": token['contract_address'],
        "network": network,
        "poolAddress": token['pool_address'],
        "timestamp": unix_timestamp
    }
    
    print(f"   📡 Calling edge function with:")
    print(f"      Network: {network}")
    print(f"      Timestamp: {unix_timestamp} ({datetime.fromtimestamp(unix_timestamp)})")
    
    edge_req = urllib.request.Request(
        edge_function_url,
        data=json.dumps(request_data).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {service_key}',
            'Content-Type': 'application/json'
        },
        method='POST'
    )
    
    try:
        edge_response = urllib.request.urlopen(edge_req)
        result = json.loads(edge_response.read().decode())
        
        if result.get('price'):
            print(f"   ✅ SUCCESS! Price: ${result['price']}")
        else:
            print(f"   💀 No price found (dead token)")
            
        print(f"   Response: {json.dumps(result, indent=6)[:200]}...")
        
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        print(f"   ❌ HTTP Error {e.code}: {error_body[:100]}")
    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

print("\n\n🤔 HYPOTHESIS: These tokens weren't processed because:")
print("1. They were added after our batch processing started")
print("2. The processor may have had a cutoff date filter")
print("3. They might have been skipped due to rate limiting")
print("\nAll these tokens appear to be processable!")