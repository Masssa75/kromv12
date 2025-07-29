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

def get_recent_calls_with_prices():
    """Get 10 recent calls from last 48 hours that have KROM price data"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += "?select=*"
    url += "&raw_data->trade->buyPrice=not.is.null"
    url += "&raw_data->token->pa=not.is.null"
    # Get calls from last 48 hours
    two_days_ago = int((datetime.now().timestamp() - 48*3600))
    url += f"&raw_data->trade->buyTimestamp=gte.{two_days_ago}"
    url += "&order=buy_timestamp.desc"
    url += "&limit=10"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        return data
    except Exception as e:
        print(f"Error fetching calls: {e}")
        return []

def test_edge_function(contract, network, timestamp, pool_address):
    """Call edge function and get price"""
    edge_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-single"
    
    payload = {
        "contractAddress": contract,
        "network": network,
        "callTimestamp": timestamp,
        "poolAddress": pool_address
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(edge_url, data=data)
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')
    
    try:
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode())
        return result.get('priceAtCall'), result.get('callDate')
    except Exception as e:
        return None, None

print("=== Testing 10 Recent Calls (Last 48 Hours) ===")
print(f"Date: {datetime.now()}")
print()

# Get recent calls
calls = get_recent_calls_with_prices()
print(f"Found {len(calls)} recent calls with price data\n")

# Print header
print(f"{'#':<3} {'Token':<10} {'Date':<20} {'KROM Price':<15} {'Edge Price':<15} {'Difference':<12} {'Status'}")
print("-" * 95)

# Test each call
results = []
for i, call in enumerate(calls):
    raw_data = call['raw_data']
    token = raw_data.get('token', {})
    trade = raw_data.get('trade', {})
    
    ticker = token.get('symbol', 'UNKNOWN')
    krom_price = trade.get('buyPrice', 0)
    buy_timestamp = trade.get('buyTimestamp', 0)
    contract = token.get('ca', '')
    network = token.get('network', 'solana')
    pool_address = token.get('pa', '')
    
    # Format date
    buy_date = datetime.fromtimestamp(buy_timestamp).strftime('%Y-%m-%d %H:%M')
    
    # Call edge function
    edge_price, edge_date = test_edge_function(contract, network, buy_timestamp, pool_address)
    
    # Calculate difference
    if edge_price and krom_price:
        diff_pct = ((edge_price - krom_price) / krom_price) * 100
        diff_str = f"{diff_pct:+.1f}%"
        
        # Status based on difference
        if abs(diff_pct) < 5:
            status = "✅ Excellent"
        elif abs(diff_pct) < 20:
            status = "⚠️  OK"
        else:
            status = "❌ Large"
            
        results.append({
            'ticker': ticker,
            'diff': diff_pct,
            'krom_price': krom_price,
            'edge_price': edge_price
        })
    else:
        diff_str = "N/A"
        status = "❓ No data"
    
    # Format prices
    krom_price_str = f"${krom_price:.8f}" if krom_price else "N/A"
    edge_price_str = f"${edge_price:.8f}" if edge_price else "None"
    
    # Print row
    print(f"{i+1:<3} {ticker:<10} {buy_date:<20} {krom_price_str:<15} {edge_price_str:<15} {diff_str:<12} {status}")
    
    # Rate limit
    time.sleep(0.5)

# Summary statistics
print("\n" + "="*95)
print("SUMMARY:")

if results:
    diffs = [r['diff'] for r in results]
    avg_diff = sum(diffs) / len(diffs)
    print(f"Average difference: {avg_diff:+.2f}%")
    print(f"Calls with edge price: {len(results)}/{len(calls)}")
    print(f"Within 5%: {sum(1 for d in diffs if abs(d) < 5)}/{len(results)}")
    print(f"Within 20%: {sum(1 for d in diffs if abs(d) < 20)}/{len(results)}")
    
    # Show best and worst
    print("\nBest matches:")
    sorted_results = sorted(results, key=lambda x: abs(x['diff']))
    for r in sorted_results[:3]:
        print(f"  {r['ticker']}: {r['diff']:+.1f}%")
    
    print("\nWorst matches:")
    for r in sorted_results[-3:]:
        print(f"  {r['ticker']}: {r['diff']:+.1f}%")
else:
    print("No valid price comparisons available")

# Test without timezone adjustment for comparison
print("\n" + "="*95)
print("TESTING: What if we remove the UTC+7 adjustment?")
print("(Testing first 3 tokens only)")
print()

for i, call in enumerate(calls[:3]):
    raw_data = call['raw_data']
    token = raw_data.get('token', {})
    trade = raw_data.get('trade', {})
    
    ticker = token.get('symbol', 'UNKNOWN')
    krom_price = trade.get('buyPrice', 0)
    buy_timestamp = trade.get('buyTimestamp', 0)
    
    # Add back 7 hours to counteract the edge function's adjustment
    adjusted_timestamp = buy_timestamp + 25200
    
    contract = token.get('ca', '')
    network = token.get('network', 'solana')
    pool_address = token.get('pa', '')
    
    edge_price, _ = test_edge_function(contract, network, adjusted_timestamp, pool_address)
    
    if edge_price and krom_price:
        diff_pct = ((edge_price - krom_price) / krom_price) * 100
        print(f"{ticker}: KROM=${krom_price:.8f}, Edge=${edge_price:.8f}, Diff={diff_pct:+.1f}%")
    else:
        print(f"{ticker}: No edge price returned")
    
    time.sleep(0.5)