import json
import urllib.request

# Direct GeckoTerminal API call to find pools for DOGSHIT
contract = "8AKBy6SkaerTMWZAad47AYk4yKWo2Kx6R3VWzJ3zpump"
network = "solana"
krom_pool = "8MwvGfxqAuMAT1VxLFPrCzDyQKBZfUvfBYXKSuJp5cLi"

print("=== Checking Auto-Selected Pool vs KROM Pool ===")
print(f"KROM pool: {krom_pool}")
print()

# Get all pools for this token
url = f"https://api.geckoterminal.com/api/v2/networks/{network}/tokens/{contract}/pools"

req = urllib.request.Request(url)
try:
    response = urllib.request.urlopen(req)
    data = json.loads(response.read().decode())
    
    pools = data.get('data', [])
    print(f"Found {len(pools)} pools for DOGSHIT\n")
    
    # Sort by liquidity (same logic as edge function)
    sorted_pools = sorted(pools, key=lambda p: float(p['attributes'].get('reserve_in_usd', '0')), reverse=True)
    
    for i, pool in enumerate(sorted_pools[:3]):
        attrs = pool['attributes']
        pool_addr = attrs['address']
        liquidity = float(attrs.get('reserve_in_usd', '0'))
        
        print(f"{i+1}. Pool: {pool_addr}")
        print(f"   Liquidity: ${liquidity:,.2f}")
        
        if pool_addr == krom_pool:
            print(f"   ✅ This is KROM's pool!")
        if i == 0:
            print(f"   📌 This would be auto-selected (most liquid)")
        
        print()
    
    # Check if top pool matches KROM pool
    if sorted_pools and sorted_pools[0]['attributes']['address'] == krom_pool:
        print("=== CONCLUSION ===")
        print("✅ KROM's pool IS the most liquid pool!")
        print("That's why we get the same price with or without specifying the pool.")
    else:
        print("=== CONCLUSION ===")
        print("❌ KROM's pool is NOT the most liquid pool")
        print("The edge function should return different prices")
        
except Exception as e:
    print(f"Error: {e}")