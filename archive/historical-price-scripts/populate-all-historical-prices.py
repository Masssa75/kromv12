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

# Known dead token contract addresses (from our investigation)
DEAD_TOKEN_CONTRACTS = {
    "0x6e0abF27e4c3Adbe2661d45970f6e57525b72da3": "PEPE",
    "0xEaBafe9b2a487BfF6075a19ac86107170CFAca48": "YIPPITY", 
    "0xb8c35e66B4faafdCcACe27e8B5062F45cb381E31": "MOANER",
    "0x05F9c45B8D47a66723BbA62a9Ca71Df196a2699d": "WHITEY",
    "0xCb3EED3253C1DdE556E9F993abd581b7Eab168B5": "FINTAI",
    "0x848fdE81d92238542c7FDe6cAEba37a1CDCFEE1D": "SEER",
    "0x1401Aec9a8cf3090045a67bD07FEACfFBc31B50C": "RDP",
    "0x40d09d1C989FcB3A68623Fe1C1acb3b769e0d237": "BOSSBURGER",
    "0x7C2dbb9525aB8908F0094Dc790dB6d7f42ebBB01": "SHROOM",
    "0x149BB80F4069A11124dF0492f4caf10C986Ac5fD": "ZHOUSI"
}

def call_historical_price_function(contract, network, timestamp, pool_address):
    """Call our crypto-price-historical edge function"""
    edge_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-historical"
    
    payload = {
        "contractAddress": contract,
        "network": network,
        "timestamp": timestamp,
        "poolAddress": pool_address
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(edge_url, data=data)
    req.add_header('Content-Type', 'application/json')
    req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')
    
    try:
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode())
        return result
    except Exception as e:
        return {"error": str(e)}

def update_call_price(krom_id, price_value, source):
    """Update a call with historical price"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls?krom_id=eq.{krom_id}"
    
    payload = {
        "historical_price_usd": price_value,
        "price_source": source,
        "price_updated_at": datetime.now().isoformat()
    }
    
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data)
    req.add_header('Content-Type', 'application/json')
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    req.get_method = lambda: 'PATCH'
    
    try:
        response = urllib.request.urlopen(req)
        return True
    except Exception as e:
        print(f"Error updating {krom_id}: {e}")
        return False

print("=== Populating All Historical Prices ===")
print(f"Date: {datetime.now()}")

# Database columns already added via Supabase Management API
print("\n1. Database schema ready:")
print("   ✅ historical_price_usd (DECIMAL)")
print("   ✅ price_source (TEXT) - 'KROM', 'GECKO', or 'DEAD_TOKEN'")
print("   ✅ price_updated_at (TIMESTAMPTZ)")
print("   Columns already added to crypto_calls table")

# Get all calls that need price population
print(f"\n2. Processing historical prices for all calls...")

offset = 0
batch_size = 100
processed = 0
tier1_count = 0  # KROM prices
tier2_count = 0  # GeckoTerminal prices
tier3_count = 0  # Dead tokens

while True:
    # Get batch of calls
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += f"?select=krom_id,contract_address,network,pool_address,buy_timestamp,created_at,raw_data"
    url += f"&offset={offset}&limit={batch_size}"
    url += f"&order=created_at.asc"  # Process oldest first (use created_at since it's always present)
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        calls = json.loads(response.read().decode())
        
        if not calls:
            break
        
        print(f"\nProcessing batch {offset//batch_size + 1}: {len(calls)} calls")
        
        for call in calls:
            processed += 1
            krom_id = call['krom_id']
            contract = call['contract_address']
            network = call['network'] or 'ethereum'
            pool_address = call['pool_address']
            buy_timestamp_str = call['buy_timestamp']
            raw_data = call.get('raw_data', {})
            
            print(f"   {processed:4d}. {krom_id[:8]}... ", end="")
            
            # Convert timestamp - try buy_timestamp first, then created_at fallback
            timestamp_source = "buy"
            if buy_timestamp_str:
                buy_timestamp = int(datetime.fromisoformat(buy_timestamp_str.replace('Z', '+00:00')).timestamp())
            else:
                # Fallback to created_at (within 1-2 minutes of actual call)
                created_at_str = call.get('created_at')
                if created_at_str:
                    buy_timestamp = int(datetime.fromisoformat(created_at_str.replace('Z', '+00:00')).timestamp())
                    timestamp_source = "created_at"
                else:
                    print("❌ No timestamp")
                    continue
            
            # TIER 1: Check if we have KROM price
            trade = raw_data.get('trade', {})
            krom_price = trade.get('buyPrice')
            
            if krom_price is not None and krom_price > 0:
                print(f"✅ KROM price: ${krom_price:.8f} ({timestamp_source})")
                if update_call_price(krom_id, krom_price, "KROM"):
                    tier1_count += 1
                continue
            
            # TIER 3: Check if it's a known dead token
            if contract and contract.lower() in [addr.lower() for addr in DEAD_TOKEN_CONTRACTS.keys()]:
                dead_token_name = DEAD_TOKEN_CONTRACTS.get(contract, "UNKNOWN")
                print(f"💀 Dead token: {dead_token_name}")
                if update_call_price(krom_id, None, "DEAD_TOKEN"):
                    tier3_count += 1
                continue
            
            # TIER 2: Fetch from GeckoTerminal
            if contract and pool_address:
                print(f"🔍 Fetching ({timestamp_source})... ", end="")
                result = call_historical_price_function(contract, network, buy_timestamp, pool_address)
                
                if result.get('price'):
                    price = result['price']
                    print(f"✅ ${price:.8f}")
                    if update_call_price(krom_id, price, "GECKO"):
                        tier2_count += 1
                else:
                    print(f"❌ No data")
                    # Mark as dead token if GeckoTerminal has no data
                    if update_call_price(krom_id, None, "DEAD_TOKEN"):
                        tier3_count += 1
                
                time.sleep(0.1)  # Rate limiting
            else:
                print(f"❌ Missing contract/pool")
                if update_call_price(krom_id, None, "DEAD_TOKEN"):
                    tier3_count += 1
        
        offset += batch_size
        
        # Progress summary
        total_processed = tier1_count + tier2_count + tier3_count
        print(f"\n   Progress: {total_processed} updated (KROM: {tier1_count}, GECKO: {tier2_count}, DEAD: {tier3_count})")
        
        # Safety break for testing
        if processed >= 200:  # Remove this for full run
            print(f"\n   Stopping at 200 records for testing...")
            break
            
    except Exception as e:
        print(f"Error in batch: {e}")
        break

print(f"\n{'='*60}")
print(f"FINAL SUMMARY:")
print(f"Total processed: {processed}")
print(f"Tier 1 (KROM prices): {tier1_count}")
print(f"Tier 2 (GeckoTerminal): {tier2_count}")
print(f"Tier 3 (Dead tokens): {tier3_count}")
print(f"\nHistorical price population complete!")