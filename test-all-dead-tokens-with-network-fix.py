#!/usr/bin/env python3
import json
import urllib.request
import time

print("=== Testing All 'Dead' Tokens with Network Mapping Fix ===")
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

# Get all calls marked as DEAD_TOKEN
query_url = f"{supabase_url}?select=krom_id,ticker,network,pool_address,contract_address&price_source=eq.DEAD_TOKEN&order=created_at.desc&limit=50"
print(f"Finding all tokens marked as DEAD_TOKEN...")

req = urllib.request.Request(query_url)
req.add_header('apikey', service_key)
req.add_header('Authorization', f'Bearer {service_key}')

try:
    response = urllib.request.urlopen(req)
    calls = json.loads(response.read().decode())
    
    print(f"Found {len(calls)} tokens marked as DEAD_TOKEN")
    print()
    
    # Test each one with network mapping
    revivals = []
    
    for i, call in enumerate(calls):
        ticker = call.get('ticker', 'Unknown')
        network = call.get('network', 'unknown')
        pool = call.get('pool_address')
        contract = call.get('contract_address')
        krom_id = call.get('krom_id')
        
        print(f"{i+1}. {ticker} ({network})")
        
        if not pool:
            print("   ❌ No pool address - skipping")
            continue
            
        # Map network name
        mapped_network = network.lower()
        if network.lower() == 'ethereum':
            mapped_network = 'eth'
        elif network.lower() == 'solana':
            mapped_network = 'solana'
        elif network.lower() == 'bsc':
            mapped_network = 'bsc'
        
        # Test with mapped network
        test_url = f"https://api.geckoterminal.com/api/v2/networks/{mapped_network}/pools/{pool}"
        
        test_req = urllib.request.Request(test_url)
        test_req.add_header('User-Agent', 'Mozilla/5.0')
        
        try:
            test_response = urllib.request.urlopen(test_req)
            test_data = json.loads(test_response.read().decode())
            test_price = test_data.get('data', {}).get('attributes', {}).get('base_token_price_usd')
            
            if test_price and float(test_price) > 0:
                price = float(test_price)
                print(f"   ✅ REVIVED! Price: ${price:.8f}")
                revivals.append({
                    'krom_id': krom_id,
                    'ticker': ticker,
                    'network': network,
                    'pool': pool,
                    'price': price
                })
            else:
                print("   💀 Still no price data")
                
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print("   💀 Still 404 - genuinely dead")
            else:
                print(f"   ❌ HTTP Error: {e.code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Rate limiting
        time.sleep(0.1)
    
    print(f"\n{'='*60}")
    print(f"REVIVAL SUMMARY:")
    print(f"Total dead tokens tested: {len(calls)}")
    print(f"Tokens revived: {len(revivals)}")
    
    if revivals:
        print(f"\n🎉 REVIVED TOKENS:")
        for revival in revivals:
            print(f"  {revival['ticker']}: ${revival['price']:.8f} (ID: {revival['krom_id']})")
        
        print(f"\n💡 Next steps:")
        print(f"1. These tokens should be deleted from database")
        print(f"2. Let crypto-poller re-fetch them with correct prices")
        print(f"3. Or update their price_source and historical_price_usd directly")
    else:
        print(f"\n✅ No additional revivals found")
        print(f"The network mapping fix mainly helps with ethereum->eth conversion")
        
except Exception as e:
    print(f"❌ Error: {e}")