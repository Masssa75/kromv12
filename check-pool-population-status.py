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

def count_with_condition(condition):
    """Count calls with a specific condition"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=krom_id&{condition}"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    req.add_header('Range', '0-10000')
    req.add_header('Prefer', 'count=exact')
    
    try:
        response = urllib.request.urlopen(req)
        content_range = response.headers.get('content-range')
        if content_range:
            return int(content_range.split('/')[-1])
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 0

print("=== Pool Address Population Status ===\n")

# Count different scenarios
total_calls = count_with_condition("limit=1")  # Total calls
has_pool_in_raw = count_with_condition("raw_data->token->pa=not.is.null")
has_pool_column = count_with_condition("pool_address=not.is.null")
needs_population = count_with_condition("raw_data->token->pa=not.is.null&pool_address=is.null")

print(f"Total calls in database: {total_calls:,}")
print(f"Calls with pool in raw_data.token.pa: {has_pool_in_raw:,}")
print(f"Calls with pool_address populated: {has_pool_column:,}")
print(f"Calls still needing population: {needs_population:,}")

if has_pool_in_raw > 0:
    progress = has_pool_column / has_pool_in_raw * 100
    print(f"\nProgress: {progress:.1f}% complete")

# Show a few examples
url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
url += "?select=ticker,pool_address,raw_data->token->pa"
url += "&pool_address=not.is.null"
url += "&limit=5"
url += "&order=updated_at.desc.nullsfirst,created_at.desc"

req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)

try:
    response = urllib.request.urlopen(req)
    examples = json.loads(response.read().decode())
    
    if examples:
        print("\nRecently populated examples:")
        for ex in examples:
            pa = ex.get('pa', 'N/A')
            print(f"- {ex.get('ticker')}: pool_address={ex.get('pool_address', 'None')[:30]}...")
except Exception as e:
    print(f"Error getting examples: {e}")