import json
import urllib.request
import time
from datetime import datetime

def search_by_contract_address(network, contract_address, token_name):
    """Search for pools using the token contract address"""
    base_url = "https://api.geckoterminal.com/api/v2"
    
    print(f"\n--- Searching by Contract: {token_name} ---")
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
                price_usd = attrs.get('base_token_price_usd')
                
                print(f"   Pool {i+1}: {pool_addr}")
                print(f"      Name: {pool_name}")
                print(f"      Liquidity: ${liquidity:,.2f}")
                print(f"      Price: ${float(price_usd) if price_usd else 0:.8f}")
                
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

print("=== Finding Correct Pools for 'Dead' Tokens ===")
print(f"Date: {datetime.now()}")

# Test the tokens that showed as dead
test_cases = [
    {
        "name": "$OPTI",
        "network": "ethereum", 
        "contract": "0x05E651Fe74f82598f52Da6C5761C02b7a8f56fCa",
        "krom_pool": "0xd23EA6834ea57A65797303AECaDF74eDff9FA095"
    },
    {
        "name": "HONOKA",
        "network": "ethereum",
        "contract": "0x8d9779A08A5E38e8b5A28bd31E50b8cd3D238Ed8",
        "krom_pool": "0x0Ee732251ce31fF8349561E1408d7828B86FB5Dd"
    }
]

findings = []

for case in test_cases:
    print(f"\n{'='*80}")
    print(f"INVESTIGATING: {case['name']}")
    print(f"KROM pool: {case['krom_pool']}")
    
    # Search by contract address to find all pools
    pools = search_by_contract_address(case["network"], case["contract"], case["name"])
    
    if pools:
        # Check if KROM's pool address matches any found pools
        krom_pool_lower = case["krom_pool"].lower()
        pool_match = None
        
        for pool in pools:
            if pool['attributes']['address'].lower() == krom_pool_lower:
                pool_match = pool
                break
        
        if pool_match:
            print(f"\n   ✅ KROM pool address is correct!")
            print(f"   This suggests the token is actually dead or has no price data")
        else:
            print(f"\n   ⚠️  KROM pool address doesn't match any found pools!")
            print(f"   KROM might be using the wrong pool address")
            
            best_pool = pools[0]  # Highest liquidity
            correct_pool = best_pool['attributes']['address']
            price = best_pool['attributes'].get('base_token_price_usd')
            
            print(f"   💡 Suggested correct pool: {correct_pool}")
            print(f"   Price with correct pool: ${float(price) if price else 0:.8f}")
            
            findings.append({
                "token": case["name"],
                "krom_pool": case["krom_pool"],
                "correct_pool": correct_pool,
                "price": float(price) if price else 0
            })
    else:
        print(f"\n   💀 No pools found - token is genuinely dead/delisted")
    
    time.sleep(1)  # Rate limiting

print(f"\n{'='*80}")
print(f"\nFINAL ANALYSIS:")

if findings:
    print(f"🔍 Found {len(findings)} tokens with incorrect pool addresses!")
    print(f"\nCORRECTIONS NEEDED:")
    for finding in findings:
        print(f"\n{finding['token']}:")
        print(f"  Wrong pool (KROM): {finding['krom_pool']}")
        print(f"  Correct pool:     {finding['correct_pool']}")
        print(f"  Actual price:     ${finding['price']:.8f}")
    
    print(f"\n💡 SOLUTION: Update KROM's pool addresses in database")
else:
    print(f"✅ All pool addresses are correct - tokens are genuinely dead")
    print(f"The crypto-poller is working correctly")