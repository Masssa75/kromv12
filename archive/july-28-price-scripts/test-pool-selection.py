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

# Test data - SLOP token
contract = "2uaTpSujZBYwBZNXusmW7PqM8Vi4qwbyotnfWhaN9oT9"
network = "solana"
timestamp = 1753679760  # Recent SLOP timestamp
krom_price = 0.00221998

# Known pools for SLOP (from previous tests)
pools = [
    ("KROM's pool (most liquid)", "DwTSZ1Jk2H1d8Dshgyg1xBfyNhoTmbwczjM4w2FfHdA2"),
    ("Pool #2", "CmficnS6Fz91P5ycK41RXdcP8XwVoguadkzKcGEV1jQh"),
    ("Pool #3", "GL1wNNDpMHqj1EF4aQ3DWJ4xSdpyBhixMnBxzfVdQsjR"),
]

print("=== Testing Pool Selection Logic ===")
print(f"Token: SLOP")
print(f"KROM price: ${krom_price:.8f}")
print(f"Timestamp: {timestamp} ({datetime.fromtimestamp(timestamp)})")
print()

edge_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-single"
prices = {}

# Test each pool
for pool_name, pool_address in pools:
    print(f"\nTesting {pool_name}:")
    print(f"Pool: {pool_address}")
    
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
            prices[pool_name] = price
            print(f"  Price: ${price:.8f}")
            diff = ((price - krom_price) / krom_price) * 100
            print(f"  Diff from KROM: {diff:+.2f}%")
        else:
            print(f"  Price: None")
            print(f"  Response: {json.dumps(result, indent=2)}")
            
    except Exception as e:
        print(f"  Error: {e}")
    
    time.sleep(1)  # Rate limit

# Compare prices
print("\n" + "="*60)
print("PRICE COMPARISON:")
if len(set(prices.values())) > 1:
    print("✅ Different pools return DIFFERENT prices!")
    print("The edge function IS using the provided pool address.")
else:
    print("❌ All pools return the SAME price.")
    print("The edge function is NOT using the provided pool address.")
    
for pool_name, price in prices.items():
    print(f"  {pool_name}: ${price:.8f}")