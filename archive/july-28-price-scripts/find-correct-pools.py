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

def find_pools_by_contract(network, contract_address, token_name):
    """Find pools using the token contract address"""
    base_url = "https://api.geckoterminal.com/api/v2"
    
    print(f"\n=== FINDING POOLS FOR {token_name} ===")
    print(f"Contract: {contract_address}")
    print(f"Network: {network}")
    
    pools_url = f"{base_url}/networks/{network}/tokens/{contract_address}/pools"
    print(f"URL: {pools_url}")
    
    req = urllib.request.Request(pools_url)
    req.add_header('User-Agent', 'Mozilla/5.0')
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        pools = data.get('data', [])
        
        if pools:
            print(f"✅ Found {len(pools)} pools!")
            
            # Sort by liquidity
            sorted_pools = sorted(pools, key=lambda p: float(p['attributes'].get('reserve_in_usd', '0')), reverse=True)
            
            print(f"\nTop pools by liquidity:")
            for i, pool in enumerate(sorted_pools[:3]):
                attrs = pool['attributes']
                pool_addr = attrs['address']
                liquidity = float(attrs.get('reserve_in_usd', '0'))
                name = attrs.get('name', 'Unknown')
                
                print(f"  {i+1}. {pool_addr}")
                print(f"     Name: {name}")
                print(f"     Liquidity: ${liquidity:,.2f}")
                
            return sorted_pools
        else:
            print(f"❌ No pools found")
            return []
            
    except urllib.error.HTTPError as e:
        print(f"❌ HTTP Error: {e.code} - {e.reason}")
        return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []

print("=== FINDING CORRECT POOLS FOR FAILED TOKENS ===")
print(f"Date: {datetime.now()}")

# Get the actual failed tokens from database with contract addresses
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

# Focus on the failed tokens
failed_tickers = ['PEPE', 'YIPPITY', 'MOANER', 'WHITEY', 'FINTAI', 'SEER', 'RDP', 'BOSSBURGER']

print(f"Searching for correct pools...")

found_corrections = []

for call in calls:
    raw_data = call['raw_data']
    token = raw_data.get('token', {})
    trade = raw_data.get('trade', {})
    
    ticker = token.get('symbol', 'UNKNOWN')
    
    if ticker in failed_tickers:
        contract = token.get('ca', '')
        network = token.get('network', 'ethereum')
        krom_pool = token.get('pa', '')
        krom_price = trade.get('buyPrice', 0)
        timestamp = trade.get('buyTimestamp', 0)
        
        print(f"\n{'='*60}")
        print(f"Investigating {ticker}")
        print(f"KROM pool: {krom_pool}")
        print(f"KROM price: ${krom_price}")
        print(f"Timestamp: {datetime.fromtimestamp(timestamp)}")
        
        # Find correct pools
        pools = find_pools_by_contract(network, contract, ticker)
        
        if pools:
            correct_pool = pools[0]['attributes']['address']
            
            if correct_pool != krom_pool:
                print(f"\n🔍 POOL MISMATCH FOUND!")
                print(f"   KROM pool: {krom_pool}")
                print(f"   Correct pool: {correct_pool}")
                
                found_corrections.append({
                    'ticker': ticker,
                    'krom_pool': krom_pool,
                    'correct_pool': correct_pool,
                    'contract': contract,
                    'network': network,
                    'timestamp': timestamp,
                    'krom_price': krom_price
                })
            else:
                print(f"\n✅ Pool address is correct")
        
        time.sleep(1)  # Rate limit

print(f"\n{'='*60}")
print(f"\nSUMMARY:")
print(f"Found {len(found_corrections)} pool address corrections needed")

if found_corrections:
    print(f"\nREQUIRED CORRECTIONS:")
    for correction in found_corrections:
        print(f"\n{correction['ticker']}:")
        print(f"  Wrong: {correction['krom_pool']}")
        print(f"  Right: {correction['correct_pool']}")
    
    print(f"\nNext step: Update the database with correct pool addresses")
else:
    print(f"\nNo pool corrections found - tokens genuinely don't exist in GeckoTerminal")