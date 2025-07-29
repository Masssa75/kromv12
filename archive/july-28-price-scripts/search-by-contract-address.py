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

def search_by_contract_address(network, contract_address, token_name):
    """Search for pools using the token contract address"""
    base_url = "https://api.geckoterminal.com/api/v2"
    
    print(f"\n--- Searching by Contract Address: {token_name} ---")
    print(f"Contract: {contract_address}")
    print(f"Network: {network}")
    
    # Search for pools using the token contract address
    pools_url = f"{base_url}/networks/{network}/tokens/{contract_address}/pools"
    print(f"URL: {pools_url}")
    
    req = urllib.request.Request(pools_url)
    req.add_header('User-Agent', 'Mozilla/5.0')
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        pools = data.get('data', [])
        
        if pools:
            print(f"   ✅ Found {len(pools)} pools for this token!")
            
            # Show all pools with their details
            sorted_pools = sorted(pools, key=lambda p: float(p['attributes'].get('reserve_in_usd', '0')), reverse=True)
            
            for i, pool in enumerate(sorted_pools):
                attrs = pool['attributes']
                pool_addr = attrs['address']
                liquidity = float(attrs.get('reserve_in_usd', '0'))
                pool_name = attrs.get('name', 'Unknown')
                
                print(f"   Pool {i+1}: {pool_addr}")
                print(f"      Name: {pool_name}")
                print(f"      Liquidity: ${liquidity:,.2f}")
                
            return sorted_pools
        else:
            print(f"   ❌ No pools found for this token contract")
            return []
            
    except urllib.error.HTTPError as e:
        print(f"   ❌ HTTP Error: {e.code} - {e.reason}")
        return []
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return []

def search_multiple_networks(contract_address, token_name, original_network):
    """Search across multiple networks"""
    networks_to_try = ['ethereum', 'solana', 'bsc', 'polygon', 'arbitrum', 'base']
    
    print(f"\n--- Multi-Network Search for {token_name} ---")
    
    all_results = {}
    
    for network in networks_to_try:
        print(f"\nTrying {network}...")
        pools = search_by_contract_address(network, contract_address, f"{token_name} on {network}")
        if pools:
            all_results[network] = pools
            print(f"   🎯 SUCCESS: Found {len(pools)} pools on {network}!")
        time.sleep(0.3)  # Rate limiting
    
    return all_results

print("=== Searching Failed Tokens by Contract Address ===")
print(f"Date: {datetime.now()}")

# Get the 20 oldest calls to identify the failed ones
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

# Identify tokens that failed in previous tests
successful_tokens = ['TCM', 'BIP177', 'CRIPTO', 'PGUSSY', 'ASSOL', 'BUBB']
failed_calls = []

for call in calls:
    raw_data = call['raw_data']
    token = raw_data.get('token', {})
    ticker = token.get('symbol', 'UNKNOWN')
    
    # Skip successful tokens and focus on failed ones
    if ticker not in successful_tokens:
        failed_calls.append(call)

print(f"Found {len(failed_calls)} failed tokens from previous test")
print(f"Will search by contract address across all major networks...")

# Search each failed token by contract address
search_results = {}

for i, call in enumerate(failed_calls[:10]):  # Limit to 10 to avoid rate limits
    raw_data = call['raw_data']
    token = raw_data.get('token', {})
    trade = raw_data.get('trade', {})
    
    ticker = token.get('symbol', 'UNKNOWN')
    contract = token.get('ca', '')
    network = token.get('network', 'ethereum')
    pool_address = token.get('pa', '')
    krom_price = trade.get('buyPrice', 0)
    timestamp = trade.get('buyTimestamp', 0)
    
    print(f"\n{'='*80}")
    print(f"SEARCHING: {ticker} (#{i+1})")
    print(f"Original Network: {network}")
    print(f"Contract: {contract}")
    print(f"Pool (from KROM): {pool_address}")
    print(f"KROM Price: ${krom_price}")
    print(f"Timestamp: {datetime.fromtimestamp(timestamp)}")
    
    if not contract:
        print("   ❌ No contract address available")
        continue
    
    # Search across all networks
    results = search_multiple_networks(contract, ticker, network)
    
    if results:
        search_results[ticker] = {
            'contract': contract,
            'original_network': network,
            'original_pool': pool_address,
            'found_networks': results
        }
        
        print(f"\n   🎉 FOUND POOLS FOR {ticker}!")
        for net, pools in results.items():
            print(f"   {net}: {len(pools)} pools")
    else:
        print(f"\n   ❌ No pools found on any network for {ticker}")
    
    print(f"\n{'='*80}")
    time.sleep(2)  # Rate limiting between tokens

# Final summary
print(f"\n{'='*80}")
print(f"\nFINAL RESULTS:")
print(f"Tokens searched: {len([c for c in failed_calls[:10] if c['raw_data'].get('token', {}).get('ca')])}")
print(f"Tokens found on GeckoTerminal: {len(search_results)}")

if search_results:
    print(f"\nSUCCESSFUL DISCOVERIES:")
    for ticker, data in search_results.items():
        print(f"\n{ticker}:")
        print(f"  Contract: {data['contract']}")
        print(f"  Original network: {data['original_network']}")
        print(f"  Found on networks: {list(data['found_networks'].keys())}")
        
        # Check if KROM pool matches any found pools
        original_pool = data['original_pool'].lower()
        found_match = False
        
        for network, pools in data['found_networks'].items():
            for pool in pools:
                if pool['attributes']['address'].lower() == original_pool:
                    print(f"  ✅ KROM pool matches {network} pool!")
                    found_match = True
                    break
        
        if not found_match:
            print(f"  ⚠️  KROM pool doesn't match any found pools")
else:
    print(f"\nNo tokens found on GeckoTerminal by contract address")
    print(f"This confirms these tokens genuinely don't exist in GeckoTerminal's database")