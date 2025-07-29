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

def get_calls_with_prices(limit=10):
    """Get calls with buy prices"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += "?select=krom_id,ticker,raw_data"
    url += "&raw_data->trade->buyPrice=not.is.null"
    url += "&order=created_at.desc"
    url += f"&limit={limit}"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error: {e}")
        return []

def fetch_minute_candle_via_edge(contract, network, timestamp):
    """Fetch exact minute candle data using edge function"""
    edge_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-single"
    
    data = json.dumps({
        "contractAddress": contract,
        "network": network,
        "callTimestamp": timestamp,
        "debug": True  # Request debug info if supported
    }).encode('utf-8')
    
    req = urllib.request.Request(edge_url, data=data, method='POST')
    req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')
    req.add_header('Content-Type', 'application/json')
    
    try:
        response = urllib.request.urlopen(req)
        return json.loads(response.read().decode())
    except Exception as e:
        return {"error": str(e)}

def format_price(price):
    """Format price for display"""
    if price is None:
        return "None"
    if price < 0.00001:
        return f"{price:.2e}"
    elif price < 0.1:
        return f"{price:.8f}"
    else:
        return f"{price:.4f}"

print("=== Compare KROM Prices with GeckoTerminal Minute Candles ===")
print(f"Time: {datetime.now()}\n")

# Get calls
calls = get_calls_with_prices(limit=10)
print(f"Analyzing {len(calls)} calls...\n")

# Analyze each call
for i, call in enumerate(calls):
    raw_data = call.get('raw_data', {})
    trade = raw_data.get('trade', {})
    token = raw_data.get('token', {})
    
    ticker = call.get('ticker', 'Unknown')
    krom_price = trade.get('buyPrice')
    buy_timestamp = trade.get('buyTimestamp')
    contract = token.get('ca')
    network = token.get('network')
    
    if not all([krom_price, buy_timestamp, contract]):
        continue
    
    buy_time = datetime.fromtimestamp(buy_timestamp)
    
    print(f"{i+1}. {ticker} ({network})")
    print(f"   Time: {buy_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   Contract: {contract[:20]}...")
    print(f"   KROM buy price: ${format_price(krom_price)}")
    
    # Fetch candle data
    result = fetch_minute_candle_via_edge(contract, network, buy_timestamp)
    
    if "error" in result:
        print(f"   Error: {result['error']}")
    else:
        # Get the historical price (which should be from OHLCV)
        historical = result.get('priceAtCall')
        
        # For now, we're getting a single price, but let's also check
        # if we can infer open/close from the data
        print(f"   Gecko price: ${format_price(historical)}")
        
        if historical and krom_price:
            # Calculate difference
            diff_pct = ((krom_price - historical) / historical) * 100
            print(f"   Difference: {diff_pct:+.1f}%")
            
            # Analyze the difference
            if abs(diff_pct) < 1:
                print(f"   ✅ Close match!")
            elif abs(diff_pct) < 5:
                print(f"   ⚠️  Small difference")
            else:
                print(f"   ❌ Large difference")
    
    print()
    time.sleep(2)  # Rate limiting

print("\n=== Analysis Summary ===")
print("If KROM prices don't include slippage, we should see:")
print("- Differences < 1% (normal OHLC variation within a minute)")
print("- KROM price between open and close of the minute candle")
print("\nLarge differences suggest:")
print("- Different pools being tracked")
print("- Timestamp misalignment")
print("- Missing or incorrect data")

# Let's also directly call GeckoTerminal API to get raw OHLCV data
print("\n=== Direct GeckoTerminal OHLCV Test ===")
print("Testing first token directly to see raw candle data...")

if calls:
    first_call = calls[0]
    token_data = first_call.get('raw_data', {}).get('token', {})
    trade_data = first_call.get('raw_data', {}).get('trade', {})
    
    if token_data.get('ca') and trade_data.get('buyTimestamp'):
        print(f"\nToken: {first_call.get('ticker')}")
        print(f"Fetching raw OHLCV data around buy time...")
        
        # We'll need to implement direct API call or modify edge function
        # to return the full OHLCV candle data
        print("(Need to implement direct GeckoTerminal API call with proper headers)")