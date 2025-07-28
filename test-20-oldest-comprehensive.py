import json
import urllib.request
import time
from datetime import datetime

# Load environment variables
env_vars = {}
with open('.env', 'r') as f:
    for line in f:
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.strip().split('=', 1)
            env_vars[k] = v.strip()

SUPABASE_URL = env_vars['SUPABASE_URL']
SUPABASE_SERVICE_ROLE_KEY = env_vars['SUPABASE_SERVICE_ROLE_KEY']

def test_new_historical_function(contract, network, timestamp, pool_address):
    """Test the new crypto-price-historical function"""
    edge_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-historical"
    
    payload = {
        "contractAddress": contract,
        "network": network,
        "timestamp": timestamp,
        "poolAddress": pool_address
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(edge_url, data=data)
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')
    
    try:
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode())
        return result
    except Exception as e:
        return {"error": str(e)}

print("=== Testing New Function on 20 Oldest Calls with KROM Prices ===")
print(f"Date: {datetime.now()}")
print()

# Get 20 oldest calls with KROM price data
url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
url += "?select=*"
url += "&raw_data->trade->buyPrice=not.is.null"
url += "&raw_data->token->pa=not.is.null"
url += "&order=buy_timestamp.asc"  # Oldest first
url += "&limit=20"

req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)

response = urllib.request.urlopen(req)
calls = json.loads(response.read().decode())

print(f"Found {len(calls)} oldest calls with price data\n")

# Print header
print(f"{'#':<3} {'Token':<10} {'Date':<16} {'KROM Price':<15} {'New Function':<15} {'Difference':<12} {'Time Diff':<10} {'Status'}")
print("-" * 105)

# Test results storage
results = []
successful_tests = 0
within_5_percent = 0
within_20_percent = 0

# Test each call
for i, call in enumerate(calls):
    raw_data = call['raw_data']
    token = raw_data.get('token', {})
    trade = raw_data.get('trade', {})
    
    ticker = token.get('symbol', 'UNKNOWN')[:10]
    krom_price = trade.get('buyPrice', 0)
    buy_timestamp = trade.get('buyTimestamp', 0)
    contract = token.get('ca', '')
    network = token.get('network', 'solana')
    pool_address = token.get('pa', '')
    
    # Format date
    buy_date = datetime.fromtimestamp(buy_timestamp).strftime('%Y-%m-%d %H:%M')
    
    # Test new function
    result = test_new_historical_function(contract, network, buy_timestamp, pool_address)
    
    # Process results
    if "error" in result or not result.get('price'):
        new_price_str = "None"
        diff_str = "N/A"
        time_diff_str = "N/A"
        status = "❓ No data"
        
        if "error" in result:
            print(f"   Error for {ticker}: {result['error']}")
    else:
        successful_tests += 1
        new_price = result['price']
        time_difference = result.get('timeDifference', 0)
        
        new_price_str = f"${new_price:.8f}"
        time_diff_str = f"{time_difference}s"
        
        if krom_price > 0:
            diff_pct = ((new_price - krom_price) / krom_price) * 100
            diff_str = f"{diff_pct:+.1f}%"
            
            # Categorize accuracy
            if abs(diff_pct) < 5:
                status = "🎉 Excellent"
                within_5_percent += 1
                within_20_percent += 1
            elif abs(diff_pct) < 20:
                status = "✅ Good"
                within_20_percent += 1
            else:
                status = "⚠️  Large diff"
                
            results.append({
                'ticker': ticker,
                'diff': diff_pct,
                'krom_price': krom_price,
                'new_price': new_price,
                'time_diff': time_difference
            })
        else:
            diff_str = "N/A"
            status = "❓ Invalid KROM"
    
    # Format KROM price
    krom_price_str = f"${krom_price:.8f}" if krom_price else "N/A"
    
    # Print row
    print(f"{i+1:<3} {ticker:<10} {buy_date:<16} {krom_price_str:<15} {new_price_str:<15} {diff_str:<12} {time_diff_str:<10} {status}")
    
    # Rate limit to avoid overwhelming the API
    time.sleep(0.3)

# Summary statistics
print("\n" + "="*105)
print("\nDETAILED SUMMARY:")
print(f"Total calls tested: {len(calls)}")
print(f"Successful price fetches: {successful_tests}/{len(calls)} ({successful_tests/len(calls)*100:.1f}%)")

if results:
    # Calculate statistics
    differences = [abs(r['diff']) for r in results]
    avg_diff = sum(differences) / len(differences)
    
    print(f"\nACCURACY METRICS:")
    print(f"Average absolute difference: {avg_diff:.2f}%")
    print(f"Within 5% accuracy: {within_5_percent}/{len(results)} ({within_5_percent/len(results)*100:.1f}%)")
    print(f"Within 20% accuracy: {within_20_percent}/{len(results)} ({within_20_percent/len(results)*100:.1f}%)")
    
    # Show best and worst performers
    print(f"\nBEST MATCHES (smallest differences):")
    sorted_results = sorted(results, key=lambda x: abs(x['diff']))
    for r in sorted_results[:5]:
        print(f"  {r['ticker']}: {r['diff']:+.2f}% (time diff: {r['time_diff']}s)")
    
    print(f"\nWORST MATCHES (largest differences):")
    for r in sorted_results[-5:]:
        print(f"  {r['ticker']}: {r['diff']:+.2f}% (time diff: {r['time_diff']}s)")
    
    # Check time difference patterns
    time_diffs = [r['time_diff'] for r in results if r['time_diff'] is not None]
    if time_diffs:
        avg_time_diff = sum(time_diffs) / len(time_diffs)
        exact_matches = sum(1 for t in time_diffs if t == 0)
        print(f"\nTIME MATCHING:")
        print(f"Average time difference: {avg_time_diff:.1f} seconds")
        print(f"Exact timestamp matches: {exact_matches}/{len(time_diffs)} ({exact_matches/len(time_diffs)*100:.1f}%)")

print(f"\nCOMPARISON WITH OLD FUNCTION:")
print("Previous edge function results on oldest calls:")
print("- Average difference: 54-56% (very poor)")
print("- Within 5%: 0/7 (0%)")
print("- Within 20%: 0/7 (0%)")
print("\nThe new function should show SIGNIFICANT improvement!")