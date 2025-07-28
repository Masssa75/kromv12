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

def get_specific_call():
    """Get a specific call to debug in detail"""
    # Let's get the CRIPTO call that showed 36% difference
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += "?select=*"
    url += "&ticker=eq.CRIPTO"
    url += "&raw_data->trade->buyPrice=not.is.null"
    url += "&limit=1"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        return data[0] if data else None
    except Exception as e:
        print(f"Error: {e}")
        return None

def debug_edge_function_call(contract, network, timestamp):
    """Make a detailed call to edge function with debugging"""
    edge_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-single"
    
    # Log exactly what we're sending
    print("\n=== Edge Function Request ===")
    print(f"Contract: {contract}")
    print(f"Network: {network}")
    print(f"Timestamp: {timestamp}")
    print(f"Timestamp as date: {datetime.fromtimestamp(timestamp)}")
    
    data = json.dumps({
        "contractAddress": contract,
        "network": network,
        "callTimestamp": timestamp
    }).encode('utf-8')
    
    req = urllib.request.Request(edge_url, data=data, method='POST')
    req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')
    req.add_header('Content-Type', 'application/json')
    
    try:
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode())
        print("\n=== Edge Function Response ===")
        print(json.dumps(result, indent=2))
        return result
    except Exception as e:
        print(f"Error: {e}")
        return None

print("=== Debugging Price Fetching Issues ===")
print(f"Time: {datetime.now()}\n")

# Get a specific call to debug
call = get_specific_call()
if not call:
    print("No CRIPTO call found!")
    exit()

# Extract all relevant data
raw_data = call.get('raw_data', {})
trade_data = raw_data.get('trade', {})
token_data = raw_data.get('token', {})

print("=== Call Details ===")
print(f"Ticker: {call.get('ticker')}")
print(f"KROM ID: {call.get('krom_id')}")
print(f"Created at: {call.get('created_at')}")

print("\n=== Token Data ===")
print(f"Contract: {token_data.get('ca')}")
print(f"Network: {token_data.get('network')}")
print(f"Pair Address: {token_data.get('pa')}")
print(f"Pair Timestamp: {token_data.get('pairTimestamp')}")
if token_data.get('pairTimestamp'):
    print(f"Pair created: {datetime.fromtimestamp(token_data.get('pairTimestamp'))}")

print("\n=== Trade Data ===")
print(f"Buy Price: ${trade_data.get('buyPrice')}")
print(f"Buy Timestamp: {trade_data.get('buyTimestamp')}")
if trade_data.get('buyTimestamp'):
    print(f"Buy Time: {datetime.fromtimestamp(trade_data.get('buyTimestamp'))}")
print(f"Top Price: ${trade_data.get('topPrice')}")
print(f"Top Timestamp: {trade_data.get('topTimestamp')}")
if trade_data.get('topTimestamp'):
    print(f"Top Time: {datetime.fromtimestamp(trade_data.get('topTimestamp'))}")
print(f"ROI: {trade_data.get('roi')}")

# Check timestamp consistency
print("\n=== Timestamp Analysis ===")
krom_timestamp = raw_data.get('timestamp')
buy_timestamp = trade_data.get('buyTimestamp')
print(f"KROM timestamp: {krom_timestamp} ({datetime.fromtimestamp(krom_timestamp) if krom_timestamp else 'None'})")
print(f"Buy timestamp: {buy_timestamp} ({datetime.fromtimestamp(buy_timestamp) if buy_timestamp else 'None'})")
if krom_timestamp and buy_timestamp:
    diff = abs(krom_timestamp - buy_timestamp)
    print(f"Difference: {diff} seconds ({diff/60:.1f} minutes)")

# Make edge function call
if token_data.get('ca') and trade_data.get('buyTimestamp'):
    result = debug_edge_function_call(
        token_data.get('ca'),
        token_data.get('network'),
        trade_data.get('buyTimestamp')
    )
    
    if result and not result.get('error'):
        print("\n=== Price Comparison ===")
        krom_price = trade_data.get('buyPrice')
        gecko_price = result.get('priceAtCall')
        
        print(f"KROM buy price: ${krom_price}")
        print(f"Gecko historical price: ${gecko_price}")
        
        if krom_price and gecko_price:
            diff = abs(krom_price - gecko_price)
            diff_pct = (diff / krom_price) * 100
            print(f"Absolute difference: ${diff}")
            print(f"Percentage difference: {diff_pct:.1f}%")
            
            # Which is higher?
            if krom_price > gecko_price:
                print(f"KROM price is {diff_pct:.1f}% HIGHER than Gecko")
            else:
                print(f"Gecko price is {diff_pct:.1f}% HIGHER than KROM")

print("\n=== Hypothesis Testing ===")
print("1. Check if pool address matches")
if result and token_data.get('pa'):
    result_pool = result.get('poolAddress', '')
    krom_pool = token_data.get('pa', '')
    print(f"   KROM pool: {krom_pool}")
    print(f"   Gecko pool: {result_pool}")
    print(f"   Match: {'YES' if result_pool == krom_pool else 'NO'}")

print("\n2. Check exact timestamp used")
if result:
    # The edge function might be using a different timestamp
    print(f"   Requested timestamp: {trade_data.get('buyTimestamp')}")
    print(f"   Edge function might be fetching different time window")