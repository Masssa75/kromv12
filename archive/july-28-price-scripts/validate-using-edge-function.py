import json
import urllib.request
import urllib.error
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

def get_calls_with_buy_prices(limit=10):
    """Get calls that have trade.buyPrice from KROM"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += "?select=krom_id,ticker,raw_data,created_at"
    url += "&raw_data->trade->buyPrice=not.is.null"
    url += "&order=created_at.asc"  # Get oldest first
    url += f"&limit={limit}"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching calls: {e}")
        return []

def fetch_price_via_edge_function(contract_address, network, call_timestamp):
    """Use our existing edge function to fetch price"""
    edge_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-single"
    
    data = json.dumps({
        "contractAddress": contract_address,
        "network": network,
        "callTimestamp": call_timestamp
    }).encode('utf-8')
    
    req = urllib.request.Request(edge_url, data=data, method='POST')
    req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')
    req.add_header('Content-Type', 'application/json')
    
    try:
        response = urllib.request.urlopen(req)
        return json.loads(response.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        return {"error": f"HTTP {e.code}: {error_body}"}
    except Exception as e:
        return {"error": str(e)}

def format_price(price):
    """Format price for display"""
    if price is None:
        return "None"
    if price < 0.00001:
        return f"${price:.2e}"
    elif price < 1:
        return f"${price:.8f}"
    else:
        return f"${price:.4f}"

print("=== Validate Historical Price Fetching via Edge Function ===")
print(f"Started at: {datetime.now()}\n")

# Get calls with known buy prices
print("Fetching calls with known buy prices from KROM...")
calls = get_calls_with_buy_prices(limit=10)

if not calls:
    print("No calls found with buy prices!")
    exit()

print(f"Found {len(calls)} calls with buy prices\n")

# Test each call
successful_matches = 0
total_tested = 0

for i, call in enumerate(calls):
    raw_data = call.get('raw_data', {})
    trade_data = raw_data.get('trade', {})
    token_data = raw_data.get('token', {})
    
    # Extract data
    krom_id = call.get('krom_id')
    ticker = call.get('ticker', 'Unknown')
    krom_buy_price = trade_data.get('buyPrice')
    buy_timestamp = trade_data.get('buyTimestamp')
    contract = token_data.get('ca')
    network = token_data.get('network', 'unknown')
    
    if not all([krom_buy_price, buy_timestamp, contract]):
        print(f"{i+1}. {ticker} - Missing required data")
        continue
    
    buy_date = datetime.fromtimestamp(buy_timestamp).strftime('%Y-%m-%d %H:%M:%S')
    
    print(f"{i+1}. {ticker} ({network})")
    print(f"   Contract: {contract[:16]}...")
    print(f"   Buy time: {buy_date}")
    print(f"   KROM buy price: {format_price(krom_buy_price)}")
    
    # Fetch via edge function
    result = fetch_price_via_edge_function(contract, network, buy_timestamp)
    
    if "error" in result:
        print(f"   Edge function error: {result['error']}")
    else:
        historical_price = result.get('priceAtCall')
        current_price = result.get('currentPrice')
        
        print(f"   Historical price: {format_price(historical_price)}")
        print(f"   Current price: {format_price(current_price)}")
        
        # Calculate difference
        if historical_price and krom_buy_price:
            diff_percent = abs(historical_price - krom_buy_price) / krom_buy_price * 100
            print(f"   Difference: {diff_percent:.2f}%")
            
            # Consider it a match if within 5%
            if diff_percent < 5:
                print(f"   ✅ MATCH!")
                successful_matches += 1
            else:
                print(f"   ⚠️  Significant difference ({diff_percent:.1f}%)")
                # Show more details for debugging
                print(f"   Debug: KROM says ${krom_buy_price:.10f}, Gecko says ${historical_price:.10f}")
    
    total_tested += 1
    print()
    
    # Rate limiting
    time.sleep(2)

print(f"\n{'='*60}")
print(f"=== Summary ===")
print(f"Total tested: {total_tested}")
print(f"Successful matches: {successful_matches}")
if total_tested > 0:
    print(f"Success rate: {successful_matches/total_tested*100:.1f}%")
print(f"{'='*60}")

# If we have failures, let's analyze why
if successful_matches < total_tested:
    print("\n=== Analysis of Mismatches ===")
    print("Possible reasons for price differences:")
    print("1. GeckoTerminal might be tracking a different pool")
    print("2. Timing differences (KROM exact trade vs nearest minute candle)")
    print("3. Price impact/slippage not reflected in OHLCV data")
    print("4. Different price sources (on-chain vs aggregated)")

print(f"\nCompleted at: {datetime.now()}")