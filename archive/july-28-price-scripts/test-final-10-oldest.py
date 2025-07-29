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

def get_direct_price(network, pool_address, timestamp):
    """Get price directly from GeckoTerminal API"""
    base_url = "https://api.geckoterminal.com/api/v2"
    url = f"{base_url}/networks/{network}/pools/{pool_address}/ohlcv/minute"
    url += f"?before_timestamp={timestamp + 300}&limit=10&currency=usd"
    
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0')
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        ohlcv_list = data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
        
        # Find closest candle within 60 seconds
        for candle in ohlcv_list:
            if abs(candle[0] - timestamp) <= 60:
                return candle[4]  # close price
        
        # If no exact match, get closest
        if ohlcv_list:
            closest = min(ohlcv_list, key=lambda x: abs(x[0] - timestamp))
            if abs(closest[0] - timestamp) <= 300:  # within 5 minutes
                return closest[4]
                
    except:
        pass
    return None

def test_edge_function(contract, network, timestamp, pool_address):
    """Call edge function"""
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
        return result.get('priceAtCall')
    except:
        return None

print("=== Final Test: 10 Oldest Calls - Edge vs Direct API ===")
print(f"Date: {datetime.now()}")
print()

# Get oldest calls
url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
url += "?select=*"
url += "&raw_data->trade->buyPrice=not.is.null"
url += "&raw_data->token->pa=not.is.null"
url += "&order=buy_timestamp.asc"
url += "&limit=10"

req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)

response = urllib.request.urlopen(req)
calls = json.loads(response.read().decode())

print(f"{'#':<3} {'Token':<10} {'Date':<16} {'KROM Price':<12} {'Edge Price':<12} {'Direct API':<12} {'Edge Diff':<10} {'Direct Diff':<10}")
print("-" * 100)

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
    
    buy_date = datetime.fromtimestamp(buy_timestamp).strftime('%Y-%m-%d %H:%M')
    
    # Get prices
    edge_price = test_edge_function(contract, network, buy_timestamp, pool_address)
    time.sleep(0.3)
    direct_price = get_direct_price(network, pool_address, buy_timestamp)
    
    # Format values
    krom_str = f"${krom_price:.6f}"
    edge_str = f"${edge_price:.6f}" if edge_price else "None"
    direct_str = f"${direct_price:.6f}" if direct_price else "None"
    
    # Calculate differences
    if edge_price and krom_price:
        edge_diff = ((edge_price - krom_price) / krom_price) * 100
        edge_diff_str = f"{edge_diff:+.1f}%"
    else:
        edge_diff_str = "N/A"
        
    if direct_price and krom_price:
        direct_diff = ((direct_price - krom_price) / krom_price) * 100
        direct_diff_str = f"{direct_diff:+.1f}%"
    else:
        direct_diff_str = "N/A"
    
    print(f"{i+1:<3} {ticker:<10} {buy_date:<16} {krom_str:<12} {edge_str:<12} {direct_str:<12} {edge_diff_str:<10} {direct_diff_str:<10}")
    
    time.sleep(0.5)

print("\n" + "="*100)
print("\nSUMMARY:")
print("- KROM Price: The price stored in KROM's database")
print("- Edge Price: Price returned by the edge function")  
print("- Direct API: Price from direct GeckoTerminal API call")
print("- Differences show how far each method is from KROM's recorded price")