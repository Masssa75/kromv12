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

SUPABASE_SERVICE_ROLE_KEY = env_vars['SUPABASE_SERVICE_ROLE_KEY']

# Test with a token and timestamp we know works
contract = "8AKBy6SkaerTMWZAad47AYk4yKWo2Kx6R3VWzJ3zpump"  # DOGSHIT
network = "solana"
timestamp = 1753670460  # 2025-07-28 09:41:00
krom_pool = "8MwvGfxqAuMAT1VxLFPrCzDyQKBZfUvfBYXKSuJp5cLi"

print("=== Verifying Pool Behavior ===")
print(f"Token: DOGSHIT")
print(f"Testing with a working pool address")
print()

# First, get all pools for this token
print("1. Getting all pools for DOGSHIT...")
pools_url = f"https://api.geckoterminal.com/api/v2/networks/{network}/tokens/{contract}/pools"

req = urllib.request.Request(pools_url)
req.add_header('User-Agent', 'Mozilla/5.0')

try:
    response = urllib.request.urlopen(req)
    data = json.loads(response.read().decode())
    pools = data.get('data', [])
    
    print(f"Found {len(pools)} pools")
    
    # Get top 2 pools
    top_pools = []
    for i, pool in enumerate(pools[:2]):
        attrs = pool['attributes']
        pool_addr = attrs['address']
        liquidity = float(attrs.get('reserve_in_usd', '0'))
        
        print(f"\nPool #{i+1}:")
        print(f"  Address: {pool_addr}")
        print(f"  Liquidity: ${liquidity:,.2f}")
        
        if pool_addr == krom_pool:
            print(f"  ✅ This is KROM's pool")
        
        top_pools.append((f"Pool #{i+1}", pool_addr))
        
except Exception as e:
    print(f"Error getting pools: {e}")
    top_pools = [("KROM pool", krom_pool)]

# Test edge function with different pools
print("\n" + "="*60)
print("\n2. Testing edge function with different pools:")

edge_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-single"

for pool_name, pool_address in top_pools:
    print(f"\n{pool_name}: {pool_address[:20]}...")
    
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
        price = result.get('priceAtCall')
        
        if price:
            print(f"  Edge function price: ${price:.8f}")
        else:
            print(f"  Edge function price: None")
            
    except Exception as e:
        print(f"  Error: {e}")
    
    time.sleep(1)

# Direct OHLCV check
print("\n" + "="*60)
print("\n3. Direct OHLCV check for same pools:")

# Adjust timestamp for UTC+7 issue
adjusted_timestamp = timestamp - 25200  # Subtract 7 hours

for pool_name, pool_address in top_pools:
    print(f"\n{pool_name}:")
    
    before_timestamp = adjusted_timestamp + 300
    url = f"https://api.geckoterminal.com/api/v2/networks/{network}/pools/{pool_address}/ohlcv/minute"
    url += f"?before_timestamp={before_timestamp}&limit=5&currency=usd"
    
    req = urllib.request.Request(url)
    req.add_header('User-Agent', 'Mozilla/5.0')
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        ohlcv_list = data.get('data', {}).get('attributes', {}).get('ohlcv_list', [])
        
        if ohlcv_list:
            # Find closest candle
            for candle in ohlcv_list:
                candle_time = candle[0]
                if abs(candle_time - adjusted_timestamp) <= 60:
                    close_price = candle[4]
                    print(f"  Direct API close price: ${close_price:.8f}")
                    print(f"  Candle time: {datetime.fromtimestamp(candle_time)}")
                    break
            else:
                print(f"  No candle within 60 seconds")
        else:
            print(f"  No OHLCV data")
            
    except Exception as e:
        print(f"  Error: {e}")
    
    time.sleep(1)

print("\n" + "="*60)
print("\nCONCLUSION:")
print("If edge function returns same price for different pools,")
print("but direct API shows different prices, there's a bug in the edge function.")