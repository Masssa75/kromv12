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

SUPABASE_URL = env_vars['SUPABASE_URL']
SUPABASE_SERVICE_ROLE_KEY = env_vars['SUPABASE_SERVICE_ROLE_KEY']

def get_count(filter_params=""):
    """Get count of records with optional filter"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=krom_id{filter_params}"
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        return len(data)
    except Exception as e:
        print(f"   Error: {e}")
        return 0

print("=== Checking Missing Pool Addresses ===")
print(f"Date: {datetime.now()}")

# Get total count of all calls
print("\n1. Getting database counts...")
print("   (This may take a moment for large datasets)")

total_calls = get_count()
print(f"   Total calls: {total_calls}")

# Get calls with pool_address populated (not null)
with_pool = get_count("&pool_address=not.is.null")
print(f"   With pool_address: {with_pool}")

# Calculate missing
without_pool = total_calls - with_pool
print(f"   Missing pool_address: {without_pool}")

# Get calls with KROM trade data - check for buyPrice in raw_data
print("\n2. Checking KROM trade data...")
print("   Sampling first 100 calls to check structure...")

# Sample some calls to understand the data structure
url = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=krom_id,raw_data&limit=100"
req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)

response = urllib.request.urlopen(req)
sample_data = json.loads(response.read().decode())

calls_with_trade_data = 0
calls_with_pool_in_data = 0

for call in sample_data:
    raw_data = call.get('raw_data', {})
    trade = raw_data.get('trade', {})
    token = raw_data.get('token', {})
    
    if trade.get('buyPrice') is not None:
        calls_with_trade_data += 1
    
    if token.get('pa') is not None:
        calls_with_pool_in_data += 1

print(f"   Sample results (first 100 calls):")
print(f"   - With trade.buyPrice: {calls_with_trade_data}/100")
print(f"   - With token.pa in raw_data: {calls_with_pool_in_data}/100")

# Estimate totals based on sample
if sample_data:
    estimated_with_trade = int((calls_with_trade_data / 100) * total_calls)
    estimated_with_pool_data = int((calls_with_pool_in_data / 100) * total_calls)
    
    print(f"\n3. Estimated totals:")
    print(f"   Estimated calls with KROM trade data: ~{estimated_with_trade} ({calls_with_trade_data}%)")
    print(f"   Estimated calls with pool data in raw_data: ~{estimated_with_pool_data} ({calls_with_pool_in_data}%)")

# Summary
print(f"\n{'='*60}")
print(f"SUMMARY:")
print(f"Total calls in database: {total_calls:,}")
print(f"Calls with pool_address populated: {with_pool:,} ({with_pool/total_calls*100:.1f}%)")
print(f"Calls missing pool_address: {without_pool:,} ({without_pool/total_calls*100:.1f}%)")

if calls_with_trade_data > 0:
    estimated_with_trade = int((calls_with_trade_data / 100) * total_calls)
    print(f"Estimated calls with KROM prices: ~{estimated_with_trade:,} ({calls_with_trade_data}%)")

print(f"\nNEXT ACTIONS:")
if without_pool > 0:
    print(f"1. 🔧 Need to populate pool_address for {without_pool:,} remaining calls")
    print(f"   Run: python3 continue-pool-population.py")

if with_pool > 0:
    print(f"2. ✅ Can start fetching current prices for {with_pool:,} calls with pool_address")
    print(f"   These are ready for crypto-price-current edge function")

if calls_with_trade_data > 0:
    estimated_ready = min(with_pool, int((calls_with_trade_data / 100) * total_calls))
    print(f"3. 🎯 Estimated {estimated_ready:,} calls have BOTH KROM prices AND pool_address")
    print(f"   These are fully ready for price tracking!")