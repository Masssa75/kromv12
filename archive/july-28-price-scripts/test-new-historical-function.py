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

print("=== Testing New crypto-price-historical Function ===")
print(f"Date: {datetime.now()}")
print()

# Get DOGSHIT for initial test
url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
url += "?select=*&ticker=eq.DOGSHIT&raw_data->trade->buyPrice=not.is.null&limit=1"

req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)

response = urllib.request.urlopen(req)
calls = json.loads(response.read().decode())

if calls:
    call = calls[0]
    raw_data = call['raw_data']
    token = raw_data['token']
    trade = raw_data['trade']
    
    ticker = token['symbol']
    krom_price = trade['buyPrice']
    buy_timestamp = trade['buyTimestamp']
    contract = token['ca']
    network = token['network']
    pool_address = token['pa']
    
    print(f"Testing with {ticker}:")
    print(f"KROM price: ${krom_price:.8f}")
    print(f"Timestamp: {buy_timestamp} = {datetime.fromtimestamp(buy_timestamp)}")
    print(f"Pool: {pool_address[:20]}...")
    print()
    
    # Test new function
    result = test_new_historical_function(contract, network, buy_timestamp, pool_address)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        print("✅ New function response:")
        print(f"   Price: ${result.get('price', 'None')}")
        print(f"   Call date: {result.get('callDate')}")
        print(f"   Time difference: {result.get('timeDifference')} seconds")
        print(f"   Duration: {result.get('duration')}s")
        
        if result.get('candle'):
            candle = result['candle']
            print(f"   Candle OHLC: ${candle['open']:.8f} / ${candle['high']:.8f} / ${candle['low']:.8f} / ${candle['close']:.8f}")
        
        # Compare with KROM price
        if result.get('price'):
            diff = ((result['price'] - krom_price) / krom_price) * 100
            print(f"   Difference from KROM: {diff:+.2f}%")
            
            if abs(diff) < 5:
                print("   🎉 Excellent accuracy!")
            elif abs(diff) < 20:
                print("   ✅ Good accuracy")
            else:
                print("   ⚠️  Large difference")

# Test with a few more tokens
print("\n" + "="*60)
print("\nTesting with 3 more recent tokens:")

url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
url += "?select=*"
url += "&raw_data->trade->buyPrice=not.is.null"
url += "&raw_data->token->pa=not.is.null"
url += "&order=buy_timestamp.desc"
url += "&limit=3"

req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)

response = urllib.request.urlopen(req)
calls = json.loads(response.read().decode())

print(f"\n{'Token':<10} {'KROM Price':<12} {'New Function':<12} {'Difference':<12} {'Status'}")
print("-" * 60)

for call in calls:
    raw_data = call['raw_data']
    token = raw_data.get('token', {})
    trade = raw_data.get('trade', {})
    
    ticker = token.get('symbol', 'UNKNOWN')[:10]
    krom_price = trade.get('buyPrice', 0)
    buy_timestamp = trade.get('buyTimestamp', 0)
    contract = token.get('ca', '')
    network = token.get('network', 'solana')
    pool_address = token.get('pa', '')
    
    result = test_new_historical_function(contract, network, buy_timestamp, pool_address)
    
    if "error" in result or not result.get('price'):
        new_price_str = "None"
        diff_str = "N/A"
        status = "❓ No data"
    else:
        new_price = result['price']
        new_price_str = f"${new_price:.8f}"
        diff = ((new_price - krom_price) / krom_price) * 100
        diff_str = f"{diff:+.1f}%"
        
        if abs(diff) < 5:
            status = "🎉 Excellent"
        elif abs(diff) < 20:
            status = "✅ Good" 
        else:
            status = "⚠️  Large diff"
    
    krom_str = f"${krom_price:.8f}"
    print(f"{ticker:<10} {krom_str:<12} {new_price_str:<12} {diff_str:<12} {status}")
    
    time.sleep(0.5)

print("\n" + "="*60)
print("\nSUMMARY:")
print("The new crypto-price-historical function should provide:")
print("- Much better accuracy than the old edge function")
print("- Clear error handling and validation")
print("- Detailed response with candle information")
print("- Proper caching headers for historical data")