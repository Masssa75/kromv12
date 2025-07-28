#!/usr/bin/env python3
import json
import urllib.request
import time

print("=== Testing 20 Oldest Tokens with KROM Prices (Network Fix Applied) ===")
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

# Get 20 oldest calls that have KROM historical prices (buyPrice in raw_data.trade.buyPrice)
# We need to filter for calls that have trade data with buyPrice
query_url = f"{supabase_url}?select=krom_id,ticker,network,pool_address,contract_address,buy_timestamp,raw_data&raw_data->>trade.buyPrice=not.is.null&order=buy_timestamp.asc&limit=20"

print(f"Finding 20 oldest tokens with KROM historical prices...")

req = urllib.request.Request(query_url)
req.add_header('apikey', service_key)
req.add_header('Authorization', f'Bearer {service_key}')

try:
    response = urllib.request.urlopen(req)
    calls = json.loads(response.read().decode())
    
    print(f"Found {len(calls)} tokens with KROM prices")
    print()
    
    # Test each one with network mapping
    successful_fetches = 0
    failed_fetches = 0
    results = []
    
    for i, call in enumerate(calls):
        ticker = call.get('ticker', 'Unknown')
        network = call.get('network', 'unknown')
        pool = call.get('pool_address')
        krom_id = call.get('krom_id')
        raw_data = call.get('raw_data', {})
        
        # Get KROM's historical price
        krom_price = None
        try:
            krom_price = float(raw_data.get('trade', {}).get('buyPrice', 0))
        except:
            pass
            
        print(f"{i+1}. {ticker} ({network}) - KROM Price: ${krom_price:.8f}" if krom_price else f"{i+1}. {ticker} ({network}) - KROM Price: None")
        
        if not pool:
            print("   ❌ No pool address - skipping")
            failed_fetches += 1
            results.append({
                'ticker': ticker,
                'network': network,
                'krom_price': krom_price,
                'gecko_price': None,
                'status': 'NO_POOL'
            })
            continue
            
        # Map network name
        mapped_network = network.lower()
        if network.lower() == 'ethereum':
            mapped_network = 'eth'
        
        print(f"   Testing with network: {network} -> {mapped_network}")
        
        # Test with mapped network
        test_url = f"https://api.geckoterminal.com/api/v2/networks/{mapped_network}/pools/{pool}"
        
        test_req = urllib.request.Request(test_url)
        test_req.add_header('User-Agent', 'Mozilla/5.0')
        
        try:
            test_response = urllib.request.urlopen(test_req)
            test_data = json.loads(test_response.read().decode())
            gecko_price = test_data.get('data', {}).get('attributes', {}).get('base_token_price_usd')
            
            if gecko_price and float(gecko_price) > 0:
                gecko_price = float(gecko_price)
                successful_fetches += 1
                
                # Calculate difference if we have both prices
                diff_pct = None
                if krom_price and krom_price > 0:
                    diff_pct = ((gecko_price - krom_price) / krom_price) * 100
                
                print(f"   ✅ SUCCESS! Gecko: ${gecko_price:.8f}", end="")
                if diff_pct is not None:
                    print(f" (Diff: {diff_pct:+.1f}%)")
                else:
                    print()
                
                results.append({
                    'ticker': ticker,
                    'network': network,
                    'krom_price': krom_price,
                    'gecko_price': gecko_price,
                    'diff_pct': diff_pct,
                    'status': 'SUCCESS'
                })
            else:
                print("   💀 No price data")
                failed_fetches += 1
                results.append({
                    'ticker': ticker,
                    'network': network,
                    'krom_price': krom_price,
                    'gecko_price': None,
                    'status': 'NO_PRICE'
                })
                
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print("   💀 404 - dead token")
                failed_fetches += 1
                results.append({
                    'ticker': ticker,
                    'network': network,
                    'krom_price': krom_price,
                    'gecko_price': None,
                    'status': 'DEAD_404'
                })
            else:
                print(f"   ❌ HTTP Error: {e.code}")
                failed_fetches += 1
                results.append({
                    'ticker': ticker,
                    'network': network,
                    'krom_price': krom_price,
                    'gecko_price': None,
                    'status': f'HTTP_{e.code}'
                })
        except Exception as e:
            print(f"   ❌ Error: {e}")
            failed_fetches += 1
            results.append({
                'ticker': ticker,
                'network': network,
                'krom_price': krom_price,
                'gecko_price': None,
                'status': 'ERROR'
            })
        
        # Rate limiting
        time.sleep(0.3)
    
    print(f"\n{'='*80}")
    print(f"FINAL RESULTS:")
    print(f"Total tokens tested: {len(calls)}")
    print(f"Successful price fetches: {successful_fetches}")
    print(f"Failed fetches: {failed_fetches}")
    print(f"Success rate: {(successful_fetches/len(calls)*100):.1f}%")
    
    # Show comparison with previous results
    print(f"\n📊 COMPARISON:")
    print(f"Previous test (before network fix): ~8/20 = 40% success rate")
    print(f"Current test (with network fix): {successful_fetches}/20 = {(successful_fetches/20*100):.1f}% success rate")
    
    if successful_fetches > 8:
        improvement = successful_fetches - 8
        print(f"🎉 IMPROVEMENT: +{improvement} more tokens now working!")
    
    # Show breakdown by network
    network_stats = {}
    for result in results:
        network = result['network']
        status = result['status']
        if network not in network_stats:
            network_stats[network] = {'success': 0, 'failed': 0}
        
        if status == 'SUCCESS':
            network_stats[network]['success'] += 1
        else:
            network_stats[network]['failed'] += 1
    
    print(f"\n📈 BREAKDOWN BY NETWORK:")
    for network, stats in network_stats.items():
        total = stats['success'] + stats['failed']
        success_rate = (stats['success'] / total * 100) if total > 0 else 0
        print(f"  {network}: {stats['success']}/{total} = {success_rate:.1f}% success")
        
except Exception as e:
    print(f"❌ Error: {e}")