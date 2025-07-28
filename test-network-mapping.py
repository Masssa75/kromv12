#!/usr/bin/env python3
import json
import urllib.request

print("=== Testing Updated Crypto-Poller Network Mapping ===")
print()

# Let's test a few recent calls to see if they now get correct prices
# First, let's check what the most recent calls look like

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

if not service_key:
    print("❌ Could not find SUPABASE_SERVICE_ROLE_KEY in .env")
    exit(1)

# Get the 5 most recent calls with network='ethereum'
query_url = f"{supabase_url}?select=krom_id,ticker,network,pool_address,historical_price_usd,price_source&network=eq.ethereum&order=created_at.desc&limit=5"
print(f"Checking recent ethereum calls...")

req = urllib.request.Request(query_url)
req.add_header('apikey', service_key)
req.add_header('Authorization', f'Bearer {service_key}')

try:
    response = urllib.request.urlopen(req)
    calls = json.loads(response.read().decode())
    
    print(f"Found {len(calls)} recent ethereum calls:")
    print()
    
    for call in calls:
        ticker = call.get('ticker', 'Unknown')
        pool = call.get('pool_address', 'No pool')
        price = call.get('historical_price_usd')
        source = call.get('price_source', 'No source')
        
        print(f"Token: {ticker}")
        print(f"  Pool: {pool}")
        print(f"  Price: ${float(price) if price else 'None'}")
        print(f"  Source: {source}")
        
        if source == "DEAD_TOKEN" and pool and pool != 'No pool':
            # Test if this pool now works with 'eth' network
            test_url = f"https://api.geckoterminal.com/api/v2/networks/eth/pools/{pool}"
            print(f"  Testing with 'eth': ", end="")
            
            test_req = urllib.request.Request(test_url)
            test_req.add_header('User-Agent', 'Mozilla/5.0')
            
            try:
                test_response = urllib.request.urlopen(test_req)
                test_data = json.loads(test_response.read().decode())
                test_price = test_data.get('data', {}).get('attributes', {}).get('base_token_price_usd')
                
                if test_price:
                    print(f"✅ WORKS! Price: ${float(test_price):.8f}")
                else:
                    print("❌ No price data")
            except:
                print("❌ Still 404")
        
        print()
        
except Exception as e:
    print(f"❌ Error: {e}")

print("=== Next Steps ===")
print("If we see tokens still marked as DEAD_TOKEN that now work with 'eth':")
print("1. The network mapping fix is working for NEW calls")
print("2. We need to update existing records with DEAD_TOKEN status")
print("3. Or delete the recent calls and let them be re-fetched")