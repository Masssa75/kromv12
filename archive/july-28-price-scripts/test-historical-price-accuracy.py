#!/usr/bin/env python3
import json
import urllib.request
import time
from datetime import datetime

print("=== Testing Historical Price Fetching Accuracy ===")
print("Comparing KROM's stored prices vs our crypto-price-historical edge function")
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
query_url = f"{supabase_url}?select=krom_id,ticker,network,pool_address,buy_timestamp,raw_data&raw_data->>trade.buyPrice=not.is.null&order=buy_timestamp.asc&limit=20"

req = urllib.request.Request(query_url)
req.add_header('apikey', service_key)
req.add_header('Authorization', f'Bearer {service_key}')

try:
    response = urllib.request.urlopen(req)
    calls = json.loads(response.read().decode())
    
    print(f"Testing {len(calls)} oldest tokens with KROM prices...")
    print()
    
    results = []
    successful_comparisons = 0
    
    for i, call in enumerate(calls):
        ticker = call.get('ticker', 'Unknown')
        network = call.get('network', 'unknown')
        pool = call.get('pool_address')
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
        
        # Call our historical price edge function
        edge_function_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-historical"
        
        request_data = {
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
        
        try:
            edge_response = urllib.request.urlopen(edge_req)
            edge_data = json.loads(edge_response.read().decode())
            
            if edge_data.get('price'):
                historical_price = float(edge_data['price'])
                time_diff = edge_data.get('timeDifference', 0)
                
                # Calculate difference
                diff_pct = ((historical_price - krom_price) / krom_price) * 100 if krom_price > 0 else 0
                
                print(f"   Edge Function Price: ${historical_price:.8f}")
                print(f"   Time difference: {time_diff}s")
                print(f"   Price difference: {diff_pct:+.2f}%")
                
                # Consider it accurate if within 10%
                is_accurate = abs(diff_pct) <= 10
                if is_accurate:
                    print(f"   ✅ ACCURATE!")
                    successful_comparisons += 1
                else:
                    print(f"   ⚠️  Large deviation")
                
                results.append({
                    'ticker': ticker,
                    'network': network,
                    'krom_price': krom_price,
                    'historical_price': historical_price,
                    'diff_pct': diff_pct,
                    'time_diff': time_diff,
                    'accurate': is_accurate
                })
                
            else:
                print(f"   ❌ No historical price found")
                print(f"   Error: {edge_data.get('error', 'Unknown error')}")
                
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            print(f"   ❌ Edge function error: {e.code}")
            print(f"   Details: {error_body}")
        except Exception as e:
            print(f"   ❌ Error calling edge function: {e}")
        
        print()
        time.sleep(0.5)  # Rate limiting
    
    print("="*80)
    print("ACCURACY SUMMARY:")
    print(f"Total comparisons: {len(results)}")
    print(f"Accurate (within 10%): {successful_comparisons}")
    print(f"Accuracy rate: {(successful_comparisons/len(results)*100):.1f}%" if results else "N/A")
    
    if results:
        # Calculate average deviation
        deviations = [abs(r['diff_pct']) for r in results]
        avg_deviation = sum(deviations) / len(deviations)
        
        print(f"Average deviation: {avg_deviation:.2f}%")
        
        print("\nDETAILED RESULTS:")
        print(f"{'Token':<10} {'KROM Price':>12} {'Historical':>12} {'Diff %':>8} {'Accurate':>10}")
        print("-"*60)
        
        for r in sorted(results, key=lambda x: abs(x['diff_pct'])):
            accuracy = "✅" if r['accurate'] else "❌"
            print(f"{r['ticker']:<10} ${r['krom_price']:>11.8f} ${r['historical_price']:>11.8f} {r['diff_pct']:>7.1f}% {accuracy:>10}")
    
except Exception as e:
    print(f"❌ Error: {e}")