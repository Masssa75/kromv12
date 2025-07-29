#!/usr/bin/env python3
import json
import urllib.request
import time
from datetime import datetime

print("=== Testing Historical Price Fetching with Contract Address & Network Mapping ===")
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

# Get 20 oldest calls with KROM prices
supabase_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/rest/v1/crypto_calls"
query_url = f"{supabase_url}?select=krom_id,ticker,network,pool_address,contract_address,buy_timestamp,raw_data&raw_data->>trade.buyPrice=not.is.null&order=buy_timestamp.asc&limit=20"

req = urllib.request.Request(query_url)
req.add_header('apikey', service_key)
req.add_header('Authorization', f'Bearer {service_key}')

try:
    response = urllib.request.urlopen(req)
    calls = json.loads(response.read().decode())
    
    print(f"Testing {len(calls)} oldest tokens with KROM prices...")
    print("Will test both with original network names AND with mapping (ethereum->eth)")
    print()
    
    results = []
    successful_comparisons = 0
    mapping_helped_count = 0
    
    for i, call in enumerate(calls):
        ticker = call.get('ticker', 'Unknown')
        network = call.get('network', 'unknown')
        pool = call.get('pool_address')
        contract = call.get('contract_address', 'unknown')
        buy_timestamp = call.get('buy_timestamp')
        raw_data = call.get('raw_data', {})
        
        # Get KROM's historical price
        krom_price = None
        try:
            krom_price = float(raw_data.get('trade', {}).get('buyPrice', 0))
        except:
            pass
            
        if not krom_price or not pool or not buy_timestamp:
            print(f"{i+1}. {ticker} - Skipping (missing data)")
            continue
            
        print(f"{i+1}. {ticker} ({network})")
        print(f"   KROM Price: ${krom_price:.8f}")
        print(f"   Timestamp: {buy_timestamp}")
        
        # Convert timestamp to Unix timestamp
        unix_timestamp = int(datetime.fromisoformat(buy_timestamp.replace('Z', '+00:00')).timestamp())
        
        # Try with original network name first
        edge_function_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-historical"
        
        request_data = {
            "contractAddress": contract,
            "network": network,
            "poolAddress": pool,
            "timestamp": unix_timestamp
        }
        
        edge_req = urllib.request.Request(
            edge_function_url,
            data=json.dumps(request_data).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {service_key}',
                'Content-Type': 'application/json'
            },
            method='POST'
        )
        
        original_worked = False
        original_price = None
        
        try:
            edge_response = urllib.request.urlopen(edge_req)
            edge_data = json.loads(edge_response.read().decode())
            
            if edge_data.get('price'):
                original_worked = True
                original_price = float(edge_data['price'])
                time_diff = edge_data.get('timeDifference', 0)
                
                # Calculate difference
                diff_pct = ((original_price - krom_price) / krom_price) * 100 if krom_price > 0 else 0
                
                print(f"   ✅ Original network worked!")
                print(f"   Edge Function Price: ${original_price:.8f}")
                print(f"   Price difference: {diff_pct:+.2f}%")
                
                # Consider it accurate if within 10%
                is_accurate = abs(diff_pct) <= 10
                if is_accurate:
                    successful_comparisons += 1
                
                results.append({
                    'ticker': ticker,
                    'network': network,
                    'krom_price': krom_price,
                    'historical_price': original_price,
                    'diff_pct': diff_pct,
                    'accurate': is_accurate,
                    'mapping_needed': False
                })
                
        except urllib.error.HTTPError as e:
            print(f"   ❌ Original network failed: {e.code}")
            
        # If original didn't work and it's ethereum, try with 'eth'
        if not original_worked and network.lower() == 'ethereum':
            print(f"   🔄 Trying with network mapping: ethereum -> eth")
            
            request_data['network'] = 'eth'
            
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
                edge_data = json.loads(edge_response.read().decode())
                
                if edge_data.get('price'):
                    mapped_price = float(edge_data['price'])
                    time_diff = edge_data.get('timeDifference', 0)
                    
                    # Calculate difference
                    diff_pct = ((mapped_price - krom_price) / krom_price) * 100 if krom_price > 0 else 0
                    
                    print(f"   ✅ MAPPING WORKED!")
                    print(f"   Edge Function Price: ${mapped_price:.8f}")
                    print(f"   Price difference: {diff_pct:+.2f}%")
                    
                    # Consider it accurate if within 10%
                    is_accurate = abs(diff_pct) <= 10
                    if is_accurate:
                        successful_comparisons += 1
                    
                    mapping_helped_count += 1
                    
                    results.append({
                        'ticker': ticker,
                        'network': network,
                        'krom_price': krom_price,
                        'historical_price': mapped_price,
                        'diff_pct': diff_pct,
                        'accurate': is_accurate,
                        'mapping_needed': True
                    })
                else:
                    print(f"   ❌ Still no price with mapping")
                    
            except Exception as e:
                print(f"   ❌ Mapping also failed: {e}")
        
        elif not original_worked:
            print(f"   ❌ Failed and not ethereum - no mapping to try")
            
        print()
        time.sleep(0.5)  # Rate limiting
    
    print("="*80)
    print("ACCURACY SUMMARY:")
    print(f"Total successful comparisons: {len(results)}")
    print(f"Accurate (within 10%): {successful_comparisons}")
    print(f"Accuracy rate: {(successful_comparisons/len(results)*100):.1f}%" if results else "N/A")
    print(f"\n🔄 Network mapping helped: {mapping_helped_count} tokens")
    
    if results:
        # Calculate average deviation
        deviations = [abs(r['diff_pct']) for r in results]
        avg_deviation = sum(deviations) / len(deviations)
        
        print(f"Average deviation: {avg_deviation:.2f}%")
        
        print("\nDETAILED RESULTS:")
        print(f"{'Token':<10} {'KROM Price':>12} {'Historical':>12} {'Diff %':>8} {'Accurate':>10} {'Mapping':>10}")
        print("-"*70)
        
        for r in sorted(results, key=lambda x: abs(x['diff_pct'])):
            accuracy = "✅" if r['accurate'] else "❌"
            mapping = "eth→fix" if r['mapping_needed'] else "direct"
            print(f"{r['ticker']:<10} ${r['krom_price']:>11.8f} ${r['historical_price']:>11.8f} {r['diff_pct']:>7.1f}% {accuracy:>10} {mapping:>10}")
    
    # Show what failed completely
    failed_count = 20 - len(results)
    if failed_count > 0:
        print(f"\n❌ {failed_count} tokens failed completely (couldn't get historical price)")
    
except Exception as e:
    print(f"❌ Error: {e}")