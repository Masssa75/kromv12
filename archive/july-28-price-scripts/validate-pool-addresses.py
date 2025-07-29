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

def check_token_pools_alternative(network, contract_address, token_name):
    """Try to find pools for this token using the contract address"""
    base_url = "https://api.geckoterminal.com/api/v2"
    
    print(f"\n--- Alternative Pool Search for {token_name} ---")
    print(f"Contract: {contract_address}")
    print(f"Network: {network}")
    
    # Try to find pools using the token contract address
    pools_url = f"{base_url}/networks/{network}/tokens/{contract_address}/pools"
    
    req = urllib.request.Request(pools_url)
    req.add_header('User-Agent', 'Mozilla/5.0')
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        pools = data.get('data', [])
        
        if pools:
            print(f"   ✅ Found {len(pools)} pools for this token!")
            
            # Show top 3 pools by liquidity
            sorted_pools = sorted(pools, key=lambda p: float(p['attributes'].get('reserve_in_usd', '0')), reverse=True)
            
            for i, pool in enumerate(sorted_pools[:3]):
                attrs = pool['attributes']
                pool_addr = attrs['address']
                liquidity = float(attrs.get('reserve_in_usd', '0'))
                pool_name = attrs.get('name', 'Unknown')
                
                print(f"   Pool {i+1}: {pool_addr}")
                print(f"      Name: {pool_name}")
                print(f"      Liquidity: ${liquidity:,.2f}")
                
            return sorted_pools[0]['attributes']['address'] if sorted_pools else None
        else:
            print(f"   ❌ No pools found for this token contract")
            return None
            
    except Exception as e:
        print(f"   ❌ Error searching for pools: {e}")
        return None

def check_network_alternatives(contract_address, token_name, original_network):
    """Check if token exists on different networks"""
    networks_to_try = ['ethereum', 'solana', 'bsc', 'polygon', 'arbitrum', 'base']
    
    print(f"\n--- Network Search for {token_name} ---")
    
    for network in networks_to_try:
        if network == original_network:
            continue  # Skip the original network we already tried
            
        print(f"Trying {network}...")
        result = check_token_pools_alternative(network, contract_address, f"{token_name} on {network}")
        if result:
            print(f"   🎯 Found pools on {network}!")
            return network, result
        time.sleep(0.3)
    
    return None, None

print("=== Validating Pool Addresses for Failed Tokens ===")
print(f"Date: {datetime.now()}")

# Get failed tokens data
failed_cases = [
    {"ticker": "PEPE", "contract": "0xF44A6df6B24F63bc78B3ed2C1D2F0bE5BC5F3E9a", "network": "ethereum", "pool": "0x67F3Bc3B3EcBd68c79dffD22666a04e6d3f35b15"},
    {"ticker": "YIPPITY", "contract": "0x2FfaF5A1c3fE99EC1D2a01CBe1D0CC3Da4Fd8cb9", "network": "ethereum", "pool": "0xdB97400565698b3Ae7c901EE72C8920d0cd0DAD2"},
    {"ticker": "MOANER", "contract": "0xa3B8ad87BeEe8b2Bd5D62bF1A7ce2d8Bb43C5dC6", "network": "ethereum", "pool": "0x1793C59e9e8793e807c0de7330C2293bD2a76865"},
    {"ticker": "WHITEY", "contract": "0x2C74B5FF68e0d4c25FDbFA9B23Fc3C7b8892E067", "network": "ethereum", "pool": "0x1065b57045b6A1bc652859985A7094f2AcFd9048"},
    {"ticker": "FINTAI", "contract": "0x21a1c7fC6BF1a002D9cc1e6f5b8d6E39a4CCa5B4", "network": "ethereum", "pool": "0x4dE0F9891E42510367599B55D63114a125F684F0"},
]

# Test each failed case
for case in failed_cases:
    ticker = case["ticker"]
    contract = case["contract"]
    network = case["network"]
    original_pool = case["pool"]
    
    print(f"\n{'='*80}")
    print(f"INVESTIGATING: {ticker}")
    print(f"Original pool: {original_pool}")
    print(f"Original network: {network}")
    
    # 1. Try to find alternative pools on the same network
    correct_pool = check_token_pools_alternative(network, contract, ticker)
    
    if correct_pool:
        if correct_pool == original_pool:
            print(f"   ✅ Original pool address is correct")
        else:
            print(f"   ⚠️  Different pool found: {correct_pool}")
            print(f"   KROM might be using the wrong pool address")
    else:
        # 2. Try different networks
        print(f"\n   Searching other networks...")
        correct_network, correct_pool = check_network_alternatives(contract, ticker, network)
        
        if correct_network and correct_pool:
            print(f"   🎯 Token found on {correct_network} instead of {network}!")
            print(f"   Pool: {correct_pool}")
        else:
            print(f"   ❌ Token not found on any major network")
            print(f"   Possible issues:")
            print(f"   - Contract address is incorrect")
            print(f"   - Token was rugpulled/abandoned")
            print(f"   - Token is on an unsupported network")

print(f"\n{'='*80}")
print(f"\nCONCLUSION:")
print(f"This investigation will show:")
print(f"1. Whether KROM pool addresses are correct")
print(f"2. Whether tokens exist on different networks") 
print(f"3. Whether we need to update our pool address data")
print(f"4. Whether some tokens simply don't have GeckoTerminal coverage")