import json
import urllib.request
import urllib.error

# Load environment variables
env_vars = {}
with open('.env', 'r') as f:
    for line in f:
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.strip().split('=', 1)
            env_vars[k] = v.strip()

SUPABASE_URL = env_vars['SUPABASE_URL']
SUPABASE_SERVICE_ROLE_KEY = env_vars['SUPABASE_SERVICE_ROLE_KEY']

# Get one call to test
url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
url += "?select=krom_id,ticker,raw_data"
url += "&raw_data->token->pa=not.is.null"
url += "&pool_address=is.null"
url += "&limit=1"

req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)

try:
    response = urllib.request.urlopen(req)
    calls = json.loads(response.read().decode())
    
    if calls:
        call = calls[0]
        krom_id = call['krom_id']
        pool = call.get('raw_data', {}).get('token', {}).get('pa')
        
        print(f"Testing update for {call['ticker']} (ID: {krom_id})")
        print(f"Pool address: {pool}")
        
        # Try to update
        update_url = f"{SUPABASE_URL}/rest/v1/crypto_calls?krom_id=eq.{krom_id}"
        
        data = json.dumps({
            "pool_address": pool
        }).encode('utf-8')
        
        update_req = urllib.request.Request(update_url, data=data, method='PATCH')
        update_req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
        update_req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')
        update_req.add_header('Content-Type', 'application/json')
        update_req.add_header('Prefer', 'return=representation')
        
        try:
            update_response = urllib.request.urlopen(update_req)
            print(f"✅ Success! Status: {update_response.status}")
            result = json.loads(update_response.read().decode())
            print(f"Updated record: {json.dumps(result, indent=2)}")
        except urllib.error.HTTPError as e:
            print(f"❌ Error: {e}")
            print(f"Response: {e.read().decode()}")
            
except Exception as e:
    print(f"Error: {e}")