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

def check_gecko_api_directly(network, pool_address, timestamp, token_name):
    """Check GeckoTerminal API directly to diagnose issues"""
    base_url = "https://api.geckoterminal.com/api/v2"
    
    print(f"\n--- Diagnosing {token_name} ---")
    print(f"Network: {network}")
    print(f"Pool: {pool_address}")
    print(f"Timestamp: {timestamp} = {datetime.fromtimestamp(timestamp)}")
    
    # Test 1: Check if pool exists
    print(f"\n1. Testing pool existence:")
    pool_url = f"{base_url}/networks/{network}/pools/{pool_address}"
    
    req = urllib.request.Request(pool_url)
    req.add_header('User-Agent', 'Mozilla/5.0')
    
    try:
        response = urllib.request.urlopen(req)
        pool_data = json.loads(response.read().decode())
        
        if pool_data.get('data'):
            pool_attrs = pool_data['data']['attributes']
            print(f"   ✅ Pool exists!")
            print(f"   Pool name: {pool_attrs.get('name', 'Unknown')}")
            print(f"   Base token: {pool_attrs.get('base_token_price_usd', 'N/A')}")
            print(f"   Reserve USD: ${float(pool_attrs.get('reserve_in_usd', 0)):,.2f}")
        else:
            print(f"   ❌ Pool not found in response")
            return False
            
    except Exception as e:
        print(f"   ❌ Error checking pool: {e}")
        return False
    
    # Test 2: Check OHLCV data availability
    print(f"\n2. Testing OHLCV data:")
    
    # Try different time ranges
    test_ranges = [
        ("5min after", timestamp + 300),
        ("1hr after", timestamp + 3600),
        ("6hr after", timestamp + 21600),
        ("24hr after", timestamp + 86400),
    ]
    
    for range_name, before_ts in test_ranges:
        ohlcv_url = f"{base_url}/networks/{network}/pools/{pool_address}/ohlcv/minute"
        ohlcv_url += f"?before_timestamp={before_ts}&limit=10&currency=usd"
        
        req = urllib.request.Request(ohlcv_url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        
        try:
            response = urllib.request.urlopen(req)
            data = json.loads(response.read().decode())
            ohlcv_list = data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
            
            if ohlcv_list:
                print(f"   ✅ {range_name}: Found {len(ohlcv_list)} candles")
                
                # Check if any candles are close to our timestamp
                closest_diff = float('inf')
                for candle in ohlcv_list:
                    diff = abs(candle[0] - timestamp)
                    if diff < closest_diff:
                        closest_diff = diff
                
                print(f"      Closest candle: {closest_diff} seconds away")
                
                if closest_diff <= 300:  # Within 5 minutes
                    print(f"      🎯 Found usable data! Candle within 5 minutes")
                    return True
                    
            else:
                print(f"   ❌ {range_name}: No OHLCV data")
                
        except Exception as e:
            print(f"   ❌ {range_name}: Error - {e}")
        
        time.sleep(0.2)  # Rate limit
    
    # Test 3: Try hour and day intervals
    print(f"\n3. Testing other timeframes:")
    
    for interval in ['hour', 'day']:
        ohlcv_url = f"{base_url}/networks/{network}/pools/{pool_address}/ohlcv/{interval}"
        ohlcv_url += f"?before_timestamp={timestamp + 86400}&limit=5&currency=usd"
        
        req = urllib.request.Request(ohlcv_url)
        req.add_header('User-Agent', 'Mozilla/5.0')
        
        try:
            response = urllib.request.urlopen(req)
            data = json.loads(response.read().decode())
            ohlcv_list = data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
            
            if ohlcv_list:
                print(f"   ✅ {interval}: Found {len(ohlcv_list)} candles")
            else:
                print(f"   ❌ {interval}: No data")
                
        except Exception as e:
            print(f"   ❌ {interval}: Error - {e}")
            
        time.sleep(0.2)
    
    return False

print("=== Investigating Missing Data for 12 Failed Tokens ===")
print(f"Date: {datetime.now()}")

# Get the 20 oldest calls again to identify the failed ones
url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
url += "?select=*"
url += "&raw_data->trade->buyPrice=not.is.null"
url += "&raw_data->token->pa=not.is.null"
url += "&order=buy_timestamp.asc"
url += "&limit=20"

req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)

response = urllib.request.urlopen(req)
calls = json.loads(response.read().decode())

# Identify failed tokens from previous test
failed_tokens = []
successful_tokens = ['TCM', 'BIP177', 'CRIPTO', 'CRIPTO', 'PGUSSY', 'CRIPTO', 'ASSOL', 'BUBB']

for call in calls:
    raw_data = call['raw_data']
    token = raw_data.get('token', {})
    ticker = token.get('symbol', 'UNKNOWN')
    
    if ticker not in successful_tokens:
        failed_tokens.append(call)

print(f"Found {len(failed_tokens)} tokens that failed in previous test")
print("\nInvestigating each failed token in detail...")

# Investigate first 5 failed tokens in detail
for i, call in enumerate(failed_tokens[:5]):
    raw_data = call['raw_data']
    token = raw_data.get('token', {})
    trade = raw_data.get('trade', {})
    
    ticker = token.get('symbol', 'UNKNOWN')
    krom_price = trade.get('buyPrice', 0)
    buy_timestamp = trade.get('buyTimestamp', 0)
    contract = token.get('ca', '')
    network = token.get('network', 'solana')
    pool_address = token.get('pa', '')
    
    # Skip zero-price tokens
    if krom_price == 0:
        print(f"\n--- Skipping {ticker} (zero price) ---")
        continue
    
    found_data = check_gecko_api_directly(network, pool_address, buy_timestamp, ticker)
    
    if not found_data:
        print(f"\n   💡 DIAGNOSIS: {ticker} has no historical data available")
        print(f"   Possible reasons:")
        print(f"   - Pool was created after this timestamp")
        print(f"   - Pool had no trading activity at this time")
        print(f"   - Pool address is incorrect or changed")
        print(f"   - Network is incorrect")
    
    print("\n" + "="*80)
    time.sleep(1)  # Rate limit between tokens

print(f"\nSUMMARY:")
print(f"The investigation should reveal whether:")
print(f"1. Pool addresses are incorrect")
print(f"2. Pools didn't exist at those timestamps")
print(f"3. There was no trading activity")
print(f"4. Network specification is wrong")
print(f"5. GeckoTerminal doesn't have historical data that far back")