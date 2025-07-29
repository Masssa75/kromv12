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

print("=== Checking Missing Pool Addresses ===")
print(f"Date: {datetime.now()}")

# Get total count of all calls
print("\n1. Total calls in database:")
url = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=count&count=exact"
req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
req.add_header('Prefer', 'count=exact')

response = urllib.request.urlopen(req)
data = json.loads(response.read().decode())
total_calls = len(data) if isinstance(data, list) else 0

# Get count from headers if available
if hasattr(response, 'headers'):
    content_range = response.headers.get('content-range', '')
    if '/' in content_range:
        total_calls = int(content_range.split('/')[-1])

print(f"   Total calls: {total_calls}")

# Get calls with pool_address populated
print("\n2. Calls with pool_address populated:")
url = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=count&pool_address=not.is.null&count=exact"
req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
req.add_header('Prefer', 'count=exact')

response = urllib.request.urlopen(req)
data = json.loads(response.read().decode())
with_pool = len(data) if isinstance(data, list) else 0

# Try to get count from headers
if hasattr(response, 'headers'):
    content_range = response.headers.get('content-range', '')
    if '/' in content_range:
        with_pool = int(content_range.split('/')[-1])

print(f"   With pool_address: {with_pool}")

# Get calls without pool_address (missing)
print("\n3. Calls missing pool_address:")
url = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=count&pool_address=is.null&count=exact"
req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
req.add_header('Prefer', 'count=exact')

response = urllib.request.urlopen(req)
data = json.loads(response.read().decode())
without_pool = len(data) if isinstance(data, list) else 0

# Try to get count from headers
if hasattr(response, 'headers'):
    content_range = response.headers.get('content-range', '')
    if '/' in content_range:
        without_pool = int(content_range.split('/')[-1])

print(f"   Missing pool_address: {without_pool}")

# Get calls with KROM trade data (have buyPrice)
print("\n4. Calls with KROM trade data (buyPrice):")
url = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=count&raw_data->>trade.buyPrice=not.is.null&count=exact"
req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
req.add_header('Prefer', 'count=exact')

try:
    response = urllib.request.urlopen(req)
    data = json.loads(response.read().decode())
    with_trade_data = len(data) if isinstance(data, list) else 0
    
    # Try to get count from headers
    if hasattr(response, 'headers'):
        content_range = response.headers.get('content-range', '')
        if '/' in content_range:
            with_trade_data = int(content_range.split('/')[-1])
            
    print(f"   With KROM trade data: {with_trade_data}")
except Exception as e:
    print(f"   Error getting trade data count: {e}")
    with_trade_data = "Unknown"

# Get calls with both KROM trade data AND pool_address
print("\n5. Calls with BOTH KROM trade data AND pool_address:")
url = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=count&raw_data->>trade.buyPrice=not.is.null&pool_address=not.is.null&count=exact"
req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
req.add_header('Prefer', 'count=exact')

try:
    response = urllib.request.urlopen(req)
    data = json.loads(response.read().decode())
    with_both = len(data) if isinstance(data, list) else 0
    
    # Try to get count from headers
    if hasattr(response, 'headers'):
        content_range = response.headers.get('content-range', '')
        if '/' in content_range:
            with_both = int(content_range.split('/')[-1])
            
    print(f"   With BOTH: {with_both}")
except Exception as e:
    print(f"   Error getting both count: {e}")
    with_both = "Unknown"

# Summary
print(f"\n{'='*60}")
print(f"SUMMARY:")
print(f"Total calls in database: {total_calls}")
print(f"Calls with pool_address: {with_pool} ({with_pool/total_calls*100:.1f}%)")
print(f"Calls missing pool_address: {without_pool} ({without_pool/total_calls*100:.1f}%)")

if isinstance(with_trade_data, int):
    print(f"Calls with KROM trade data: {with_trade_data} ({with_trade_data/total_calls*100:.1f}%)")
    
if isinstance(with_both, int):
    print(f"Calls ready for price fetching: {with_both} ({with_both/total_calls*100:.1f}%)")

print(f"\nNEXT ACTIONS:")
if without_pool > 0:
    print(f"1. Need to populate pool_address for {without_pool} remaining calls")
    print(f"2. Run: python3 continue-pool-population.py")
    
if isinstance(with_both, int) and with_both > 0:
    print(f"3. Can start fetching current prices for {with_both} calls that have both KROM data and pool_address")