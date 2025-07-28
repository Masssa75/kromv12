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

def fetch_gecko_historical_price(contract_address, network, timestamp):
    """Fetch historical price from GeckoTerminal at specific timestamp"""
    # Convert network names to GeckoTerminal format
    network_map = {
        'ethereum': 'eth',
        'eth': 'eth',
        'solana': 'solana',
        'sol': 'solana',
        'base': 'base',
        'arbitrum': 'arbitrum'
    }
    
    gecko_network = network_map.get(network.lower(), network.lower())
    
    # GeckoTerminal OHLCV endpoint
    # We need to get minute data around the timestamp
    # Convert timestamp to the right format
    before_timestamp = timestamp + 60  # Add 1 minute buffer
    after_timestamp = timestamp - 60   # Subtract 1 minute buffer
    
    url = f"https://api.geckoterminal.com/api/v2/networks/{gecko_network}/tokens/{contract_address}/ohlcv/minute"
    url += f"?aggregate=1"  # 1 minute candles
    url += f"&before_timestamp={before_timestamp}"
    url += f"&limit=5"  # Get a few candles
    
    try:
        req = urllib.request.Request(url)
        req.add_header('Accept', 'application/json')
        
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        
        # OHLCV data format: [timestamp, open, high, low, close, volume]
        ohlcv_list = data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
        
        if not ohlcv_list:
            return None, "No OHLCV data available"
        
        # Find the candle closest to our timestamp
        closest_candle = None
        min_diff = float('inf')
        
        for candle in ohlcv_list:
            candle_timestamp = candle[0]
            diff = abs(candle_timestamp - timestamp)
            if diff < min_diff:
                min_diff = diff
                closest_candle = candle
        
        if closest_candle and min_diff < 300:  # Within 5 minutes
            # Return the close price
            return closest_candle[4], None
        else:
            return None, f"No candle within 5 minutes of timestamp"
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        return None, f"HTTP {e.code}: {error_body}"
    except Exception as e:
        return None, str(e)

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

print("=== Validate GeckoTerminal Historical Price Fetching ===")
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
    
    # Fetch from GeckoTerminal
    gecko_price, error = fetch_gecko_historical_price(contract, network, buy_timestamp)
    
    if error:
        print(f"   Gecko price: ERROR - {error}")
    else:
        print(f"   Gecko price: {format_price(gecko_price)}")
        
        # Calculate difference
        if gecko_price and krom_buy_price:
            diff_percent = abs(gecko_price - krom_buy_price) / krom_buy_price * 100
            print(f"   Difference: {diff_percent:.2f}%")
            
            # Consider it a match if within 5%
            if diff_percent < 5:
                print(f"   ✅ MATCH!")
                successful_matches += 1
            else:
                print(f"   ⚠️  Significant difference")
    
    total_tested += 1
    print()
    
    # Rate limiting for GeckoTerminal
    time.sleep(1)

print(f"\n{'='*60}")
print(f"=== Summary ===")
print(f"Total tested: {total_tested}")
print(f"Successful matches: {successful_matches}")
if total_tested > 0:
    print(f"Success rate: {successful_matches/total_tested*100:.1f}%")
print(f"{'='*60}")

print(f"\nCompleted at: {datetime.now()}")