import json
import urllib.request

# Load environment variables
env_vars = {}
with open('.env', 'r') as f:
    for line in f:
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.strip().split('=', 1)
            env_vars[k] = v.strip()

SUPABASE_SERVICE_ROLE_KEY = env_vars['SUPABASE_SERVICE_ROLE_KEY']

# Test data
contract = "2uaTpSujZBYwBZNXusmWyYUyPwNnFVRu5hVJiHETLyVs"  # SLOP
network = "solana"
timestamp = 1753662600  # Recent timestamp
krom_pool = "DwTSZ1Jk2H1d8Dshgyg1FYhBDLCc3LZK29xYTNUr5V6y"

print("=== Testing Pool Address Handling ===")
print(f"Token: SLOP on {network}")
print()

edge_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-single"

test_cases = [
    ("No pool", None),
    ("KROM's pool", krom_pool),
    ("Invalid pool format", "INVALID_POOL_ADDRESS"),
    ("Empty string pool", ""),
    ("Wrong network pool", "0x0000000000000000000000000000000000000000"),  # ETH format on Solana
]

for test_name, pool_address in test_cases:
    print(f"\nTest: {test_name}")
    if pool_address:
        print(f"Pool: {pool_address[:20]}...")
    
    payload = {
        "contractAddress": contract,
        "network": network,
        "callTimestamp": timestamp
    }
    
    if pool_address is not None:
        payload["poolAddress"] = pool_address
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(edge_url, data=data)
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')
    
    try:
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode())
        price = result.get('priceAtCall')
        current = result.get('currentPrice')
        
        print(f"  Price at call: ${price}" if price else "  Price at call: None")
        print(f"  Current price: ${current}" if current else "  Current price: None")
        
        # Check response time as indicator
        duration = result.get('duration', 'N/A')
        print(f"  Response time: {duration}s")
        
    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "="*50)
print("\nEXPECTED BEHAVIOR:")
print("- Invalid/empty pools should return None or error")
print("- Different valid pools should return different prices")
print("- Response time might indicate if pool lookup happened")