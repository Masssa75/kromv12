import json
import urllib.request
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

# Get DOGSHIT call which we tested earlier and got good results
url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
url += "?select=*"
url += "&ticker=eq.DOGSHIT"
url += "&raw_data->trade->buyPrice=not.is.null"
url += "&limit=1"

req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)

response = urllib.request.urlopen(req)
calls = json.loads(response.read().decode())

if not calls:
    print("No DOGSHIT call found")
    exit()

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

print("=== Detailed Debug: DOGSHIT Call ===")
print(f"Ticker: {ticker}")
print(f"KROM price: ${krom_price:.8f}")
print(f"Buy timestamp: {buy_timestamp}")
print(f"Buy time (raw): {datetime.fromtimestamp(buy_timestamp)}")
print(f"Contract: {contract}")
print(f"Network: {network}")
print(f"Pool: {pool_address}")
print()

# Call edge function and get full response
edge_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-single"

payload = {
    "contractAddress": contract,
    "network": network,
    "callTimestamp": buy_timestamp,
    "poolAddress": pool_address
}

print("Calling edge function with:")
print(json.dumps(payload, indent=2))
print()

data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(edge_url, data=data)
req.add_header('Content-Type', 'application/json')
req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')

try:
    response = urllib.request.urlopen(req)
    result = json.loads(response.read().decode())
    
    print("Edge function response:")
    print(json.dumps(result, indent=2))
    
    edge_price = result.get('priceAtCall')
    if edge_price and krom_price:
        diff = ((edge_price - krom_price) / krom_price) * 100
        print(f"\nPrice comparison:")
        print(f"KROM price:  ${krom_price:.8f}")
        print(f"Edge price:  ${edge_price:.8f}")
        print(f"Difference:  {diff:+.2f}%")
        
    # Check the callDate to verify timezone handling
    call_date = result.get('callDate')
    if call_date:
        print(f"\nTimezone check:")
        print(f"Original timestamp: {buy_timestamp} = {datetime.fromtimestamp(buy_timestamp)}")
        print(f"Edge function date: {call_date}")
        
        # The edge function subtracts 7 hours, so let's verify
        adjusted_ts = buy_timestamp - 25200  # 7 hours in seconds
        print(f"Expected adjusted:  {datetime.fromtimestamp(adjusted_ts)} UTC")
        
except Exception as e:
    print(f"Error: {e}")

# Now let's check a problematic recent call
print("\n" + "="*60)
print("\n=== Checking Problematic Recent Call: GASCOIN ===")

# Get GASCOIN
url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
url += "?select=*"
url += "&ticker=eq.GASCOIN"
url += "&raw_data->trade->buyPrice=not.is.null"
url += "&order=buy_timestamp.desc"
url += "&limit=1"

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
    
    print(f"Ticker: {ticker}")
    print(f"KROM price: ${krom_price:.8f}")
    print(f"Buy time: {datetime.fromtimestamp(buy_timestamp)}")
    print(f"Pool: {pool_address}")
    
    # Test edge function
    payload = {
        "contractAddress": contract,
        "network": network,
        "callTimestamp": buy_timestamp,
        "poolAddress": pool_address
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(edge_url, data=data)
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')
    
    try:
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode())
        
        edge_price = result.get('priceAtCall')
        if edge_price:
            diff = ((edge_price - krom_price) / krom_price) * 100
            print(f"\nEdge price: ${edge_price:.8f}")
            print(f"Difference: {diff:+.2f}%")
            print(f"Call date from edge: {result.get('callDate')}")
            
            # Check if this is a reasonable time difference
            if abs(diff) > 50:
                print("\n⚠️  Very large difference detected!")
                print("Possible causes:")
                print("1. Pool mismatch - edge function might be using a different pool")
                print("2. Low liquidity - price might be very volatile")
                print("3. Data issue - KROM price might be from a different source")
    except Exception as e:
        print(f"Error: {e}")