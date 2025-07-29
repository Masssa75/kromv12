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

SUPABASE_SERVICE_ROLE_KEY = env_vars['SUPABASE_SERVICE_ROLE_KEY']

# Test with DOGSHIT which we know has data
contract = "8AKBy6SkaerTMWZAad47AYk4yKWo2Kx6R3VWzJ3zpump"
network = "solana"
timestamp = 1739192459  # Recent timestamp
krom_pool = "8MwvGfxqAuMAT1VxLFPrCzDyQKBZfUvfBYXKSuJp5cLi"
krom_price = 0.00209194

print("=== Edge Function Debug Test ===")
print(f"Testing {contract[:16]}... on {network}")
print(f"KROM pool: {krom_pool[:16]}...")
print(f"KROM price: ${krom_price}")
print()

# Test 1: Without pool
print("1. Testing WITHOUT pool address:")
edge_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-single"
payload = {
    "contractAddress": contract,
    "network": network,
    "callTimestamp": timestamp
}

data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(edge_url, data=data)
req.add_header('Content-Type', 'application/json')
req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')

try:
    response = urllib.request.urlopen(req)
    result = json.loads(response.read().decode())
    print(f"   Response: {json.dumps(result, indent=2)}")
except Exception as e:
    print(f"   Error: {e}")

print("\n2. Testing WITH pool address:")
payload["poolAddress"] = krom_pool
data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(edge_url, data=data)
req.add_header('Content-Type', 'application/json')
req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')

try:
    response = urllib.request.urlopen(req)
    result = json.loads(response.read().decode())
    print(f"   Response: {json.dumps(result, indent=2)}")
except Exception as e:
    print(f"   Error: {e}")

# Test edge cases
print("\n3. Testing with WRONG pool address:")
payload["poolAddress"] = "WRONG_POOL_ADDRESS_FOR_TESTING"
data = json.dumps(payload).encode('utf-8')
req = urllib.request.Request(edge_url, data=data)
req.add_header('Content-Type', 'application/json')
req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')

try:
    response = urllib.request.urlopen(req)
    result = json.loads(response.read().decode())
    print(f"   Response: {json.dumps(result, indent=2)}")
except Exception as e:
    print(f"   Error: {e}")