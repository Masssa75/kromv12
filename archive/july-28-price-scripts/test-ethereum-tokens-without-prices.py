#!/usr/bin/env python3
import json
import urllib.request
import time

print("=== Testing Ethereum Tokens Without Prices ===")
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

# Get ethereum tokens without price data
query_url = f"{supabase_url}?select=krom_id,ticker,network,pool_address,contract_address&network=eq.ethereum&historical_price_usd=is.null&limit=30"
print(f"Finding ethereum tokens without price data...")

req = urllib.request.Request(query_url)
req.add_header('apikey', service_key)
req.add_header('Authorization', f'Bearer {service_key}')

try:
    response = urllib.request.urlopen(req)
    calls = json.loads(response.read().decode())
    
    print(f"Found {len(calls)} ethereum tokens without price data")
    print()
    
    # Test each one with 'eth' network mapping
    revivals = []
    
    for i, call in enumerate(calls):
        ticker = call.get('ticker', 'Unknown')
        pool = call.get('pool_address')
        contract = call.get('contract_address')
        krom_id = call.get('krom_id')
        
        print(f"{i+1}. {ticker}")
        
        if not pool:
            print("   ❌ No pool address - skipping")
            continue
            
        # Test with 'eth' network
        test_url = f"https://api.geckoterminal.com/api/v2/networks/eth/pools/{pool}"
        
        test_req = urllib.request.Request(test_url)
        test_req.add_header('User-Agent', 'Mozilla/5.0')
        
        try:
            test_response = urllib.request.urlopen(test_req)
            test_data = json.loads(test_response.read().decode())
            test_price = test_data.get('data', {}).get('attributes', {}).get('base_token_price_usd')
            
            if test_price and float(test_price) > 0:
                price = float(test_price)
                print(f"   ✅ FOUND PRICE! ${price:.8f}")
                revivals.append({
                    'krom_id': krom_id,
                    'ticker': ticker,
                    'pool': pool,
                    'price': price
                })
            else:
                print("   💀 No price data")
                
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print("   💀 404 - dead token")
            else:
                print(f"   ❌ HTTP Error: {e.code}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Rate limiting
        time.sleep(0.2)
        
        # Stop after finding a few to avoid hitting rate limits
        if len(revivals) >= 10:
            print(f"\n(Stopping after finding {len(revivals)} working tokens to avoid rate limits)")
            break
    
    print(f"\n{'='*60}")
    print(f"ETHEREUM REVIVAL SUMMARY:")
    print(f"Tokens tested: {min(len(calls), i+1)}")
    print(f"Tokens with prices found: {len(revivals)}")
    
    if revivals:
        print(f"\n🎉 ETHEREUM TOKENS WITH PRICES:")
        for revival in revivals:
            print(f"  {revival['ticker']}: ${revival['price']:.8f}")
        
        print(f"\n💡 These tokens can be updated with proper price data!")
        print(f"The network mapping fix (ethereum -> eth) is helping!")
    else:
        print(f"\n❌ No working prices found in this batch")
        
except Exception as e:
    print(f"❌ Error: {e}")