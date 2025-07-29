import json
import urllib.request
import os

# Load environment variables
env_vars = {}
with open('.env', 'r') as f:
    for line in f:
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.strip().split('=', 1)
            env_vars[k] = v.strip()

SUPABASE_URL = env_vars['SUPABASE_URL']
SUPABASE_SERVICE_ROLE_KEY = env_vars['SUPABASE_SERVICE_ROLE_KEY']

# IDs that were incorrectly updated with DOGSHIT data
incorrect_ids = [
    '6886d413eb25eec68caf837f',  # REMI
    '6886d2cbeb25eec68caf82f3',  # SLOP
    '6886c482eb25eec68caf7e75',  # QUOKKA
    '6886bc02eb25eec68caf7bf5'   # SPURDO
]

print("Cleaning up incorrectly updated data...\n")

for krom_id in incorrect_ids:
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls?krom_id=eq.{krom_id}"
    
    # Set raw_data to null to remove the incorrect DOGSHIT data
    data = json.dumps({
        "raw_data": None
    }).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, method='PATCH')
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')
    req.add_header('Content-Type', 'application/json')
    req.add_header('Prefer', 'return=minimal')
    
    try:
        response = urllib.request.urlopen(req)
        if response.status == 204:
            print(f"✅ Cleared incorrect data for {krom_id}")
        else:
            print(f"❌ Failed to clear data for {krom_id}")
    except Exception as e:
        print(f"❌ Error clearing {krom_id}: {e}")

print("\n✅ Cleanup completed. These tokens now have no raw_data again.")