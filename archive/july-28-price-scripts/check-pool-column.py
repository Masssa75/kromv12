import json
import urllib.request

# Load environment variables
env_vars = {}
with open('.env', 'r') as f:
    for line in f:
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.strip().split('=', 1)
            env_vars[k] = v.strip()

SUPABASE_URL = env_vars['SUPABASE_URL']
SUPABASE_SERVICE_ROLE_KEY = env_vars['SUPABASE_SERVICE_ROLE_KEY']

# Test query to see if pool_address column exists
url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
url += "?select=krom_id,ticker,pool_address,raw_data"
url += "&limit=1"

req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)

try:
    response = urllib.request.urlopen(req)
    data = json.loads(response.read().decode())
    print("✅ pool_address column exists!")
    if data:
        print(f"Sample: {data[0].get('pool_address', 'None')}")
except urllib.error.HTTPError as e:
    error_body = e.read().decode()
    if "column crypto_calls.pool_address does not exist" in error_body:
        print("❌ pool_address column does NOT exist")
    else:
        print(f"Error: {error_body[:200]}")

# Also check if contract_address exists
url2 = f"{SUPABASE_URL}/rest/v1/crypto_calls"
url2 += "?select=krom_id,ticker,contract_address"
url2 += "&limit=1"

req2 = urllib.request.Request(url2)
req2.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)

try:
    response2 = urllib.request.urlopen(req2)
    data2 = json.loads(response2.read().decode())
    print("\n✅ contract_address column exists!")
    if data2:
        print(f"Sample: {data2[0].get('contract_address', 'None')}")
except urllib.error.HTTPError as e:
    error_body = e.read().decode()
    if "column crypto_calls.contract_address does not exist" in error_body:
        print("\n❌ contract_address column does NOT exist")

# Check what's in raw_data
print("\n=== Checking raw_data for pool info ===")
url3 = f"{SUPABASE_URL}/rest/v1/crypto_calls"
url3 += "?select=ticker,raw_data->token"
url3 += "&raw_data->token->pa=not.is.null"
url3 += "&limit=3"

req3 = urllib.request.Request(url3)
req3.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)

try:
    response3 = urllib.request.urlopen(req3)
    data3 = json.loads(response3.read().decode())
    print(f"Found {len(data3)} calls with pool address in raw_data.token.pa")
    for call in data3:
        token_data = call.get('token', {})
        print(f"- {call.get('ticker')}: ca={token_data.get('ca', 'N/A')[:20]}..., pa={token_data.get('pa', 'N/A')[:20]}...")
except Exception as e:
    print(f"Error checking raw_data: {e}")