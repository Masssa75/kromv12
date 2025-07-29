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

def populate_all_pools():
    """Use SQL to populate all pool addresses at once"""
    # Use Supabase Management API to run SQL directly
    management_token = env_vars.get('SUPABASE_ACCESS_TOKEN')
    project_id = 'eucfoommxxvqmmwdbkdv'
    
    if not management_token:
        print("No SUPABASE_ACCESS_TOKEN found in .env")
        return False
    
    sql_query = """
    UPDATE crypto_calls 
    SET pool_address = raw_data->'token'->>'pa'
    WHERE raw_data->'token'->>'pa' IS NOT NULL 
    AND pool_address IS NULL;
    """
    
    url = f"https://api.supabase.com/v1/projects/{project_id}/database/query"
    
    data = json.dumps({
        "query": sql_query
    }).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, method='POST')
    req.add_header('Authorization', f'Bearer {management_token}')
    req.add_header('Content-Type', 'application/json')
    
    try:
        response = urllib.request.urlopen(req)
        result = response.read().decode()
        return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"Error: {error_body}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def check_status():
    """Check current population status"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=krom_id&pool_address=not.is.null"
    
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
    except:
        return 0

print("=== Fast Pool Address Population ===")
print(f"Started at: {datetime.now()}\n")

# Check initial status
initial_count = check_status()
print(f"Initial count with pool_address: {initial_count:,}")

# Run the update
print("\nRunning bulk update...")
success = populate_all_pools()

if success:
    print("✅ Bulk update completed!")
    
    # Wait a moment for the update to complete
    time.sleep(2)
    
    # Check final status
    final_count = check_status()
    print(f"\nFinal count with pool_address: {final_count:,}")
    print(f"Records updated: {final_count - initial_count:,}")
else:
    print("❌ Bulk update failed")

# Show some examples
print("\nChecking populated examples...")
url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
url += "?select=ticker,pool_address,raw_data"
url += "&pool_address=not.is.null"
url += "&limit=5"
url += "&order=created_at.desc"

req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)

try:
    response = urllib.request.urlopen(req)
    examples = json.loads(response.read().decode())
    
    print("\nExamples of populated pool addresses:")
    for ex in examples:
        ticker = ex.get('ticker', 'Unknown')
        pool = ex.get('pool_address', 'None')
        pool_from_raw = ex.get('raw_data', {}).get('token', {}).get('pa', 'None')
        
        print(f"- {ticker}: {pool[:40]}...")
        if pool != pool_from_raw:
            print(f"  ⚠️  Mismatch! raw_data has: {pool_from_raw[:40]}...")
except Exception as e:
    print(f"Error getting examples: {e}")

print(f"\nFinished at: {datetime.now()}")