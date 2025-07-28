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

def get_oldest_calls_with_prices():
    """Get the 10 oldest calls that have KROM price data"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += "?select=*"
    url += "&raw_data->trade->buyPrice=not.is.null"
    url += "&raw_data->token->pa=not.is.null"
    url += "&order=buy_timestamp.asc"  # Oldest first
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
        return result.get('priceAtCall'), result.get('currentPrice')
    except Exception as e:
        print(f"Error calling edge function: {e}")
        return None, None

print("=== Testing 10 Oldest Calls with KROM Price Data ===")
print(f"Date: {datetime.now()}")
print()

# Get oldest calls
calls = get_oldest_calls_with_prices()
print(f"Found {len(calls)} oldest calls with price data\n")

# Print header
print(f"{'#':<3} {'Token':<10} {'Date':<20} {'KROM Price':<15} {'Edge Price':<15} {'Difference':<12} {'Status'}")
print("-" * 95)

# Test each call
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
    edge_price, current_price = test_edge_function(contract, network, buy_timestamp, pool_address)
    
    # Calculate difference
    if edge_price and krom_price:
        diff_pct = ((edge_price - krom_price) / krom_price) * 100
        diff_str = f"{diff_pct:+.1f}%"
        
        # Status based on difference
        if abs(diff_pct) < 5:
            status = "✅ Good"
        elif abs(diff_pct) < 20:
            status = "⚠️  OK"
        else:
            status = "❌ Large"
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

valid_diffs = []
for i, call in enumerate(calls):
    raw_data = call['raw_data']
    trade = raw_data.get('trade', {})
    krom_price = trade.get('buyPrice', 0)
    
    # Get edge price again for stats
    if krom_price:
        token = raw_data.get('token', {})
        contract = token.get('ca', '')
        network = token.get('network', 'solana')
        timestamp = trade.get('buyTimestamp', 0)
        pool_address = token.get('pa', '')
        
        edge_price, _ = test_edge_function(contract, network, timestamp, pool_address)
        
        if edge_price:
            diff = ((edge_price - krom_price) / krom_price) * 100
            valid_diffs.append(diff)

if valid_diffs:
    avg_diff = sum(valid_diffs) / len(valid_diffs)
    print(f"Average difference: {avg_diff:+.2f}%")
    print(f"Calls with edge price: {len(valid_diffs)}/{len(calls)}")
    print(f"Within 5%: {sum(1 for d in valid_diffs if abs(d) < 5)}/{len(valid_diffs)}")
    print(f"Within 20%: {sum(1 for d in valid_diffs if abs(d) < 20)}/{len(valid_diffs)}")
else:
    print("No valid price comparisons available")