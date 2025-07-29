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

# The complete DOGSHIT data from KROM API
dogshit_data = {
  "token": {
    "pa": "8MwvGfxqAuMAT1VxLFPruwzUku71divymByUFRxjQUyV",
    "pairTimestamp": 1753588617,
    "network": "solana",
    "ca": "8AKBy6SkaerTMWZAad47yQxZnvrEk59DvhcHLHUsbonk",
    "symbol": "DOGSHIT",
    "imageUrl": "https://dd.dexscreener.com/ds-data/tokens/solana/8AKBy6SkaerTMWZAad47yQxZnvrEk59DvhcHLHUsbonk.png?key=824f5c"
  },
  "trade": {
    "buyPrice": 0.002091944949922135,
    "buyTimestamp": 1753670460,
    "topPrice": 0.002806418441087263,
    "topTimestamp": 1753671360,
    "roi": 1.341535512773279,
    "error": False
  },
  "hidden": False,
  "_id": "6886e357eb25eec68caf87eb",
  "groupId": "1756488143",
  "__v": 0,
  "groupName": "lowtaxsolana",
  "messageId": 19620,
  "text": "Dogshit 💡\n\nChart seems good, keeping on tabs for now\n\nhttps://dexscreener.com/solana/8MwvGfxqAuMAT1VxLFPruwzUku71divymByUFRxjQUyV",
  "timestamp": 1753670486,
  "group": {
    "stats": {
      "callFrequency": 4.96,
      "winRate30": 33,
      "profit30": 1150,
      "earlyTop50": 1,
      "lot30": 34,
      "ins30": 379
    },
    "_id": "67adf28aeb25eec68c52c64a",
    "name": "lowtaxsolana",
    "groupId": "1756488143",
    "id": "67adf28aeb25eec68c52c64a"
  },
  "id": "6886e357eb25eec68caf87eb"
}

# Update Supabase with complete data
url = f"{SUPABASE_URL}/rest/v1/crypto_calls?krom_id=eq.6886e357eb25eec68caf87eb"

data = json.dumps({
    "raw_data": dogshit_data
}).encode('utf-8')

req = urllib.request.Request(url, data=data, method='PATCH')
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')
req.add_header('Content-Type', 'application/json')
req.add_header('Prefer', 'return=minimal')

try:
    response = urllib.request.urlopen(req)
    if response.status == 204:
        print("✅ Successfully updated DOGSHIT with trade data")
    else:
        print(f"❌ Failed to update: {response.status}")
except urllib.error.HTTPError as e:
    print(f"❌ Failed to update: {e.code}")
    print(f"Response: {e.read().decode()}")

# Verify the update
print("\nVerifying update...")
verify_url = f"{SUPABASE_URL}/rest/v1/crypto_calls?krom_id=eq.6886e357eb25eec68caf87eb&select=raw_data"

verify_req = urllib.request.Request(verify_url)
verify_req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
verify_req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')

try:
    verify_response = urllib.request.urlopen(verify_req)
    if verify_response.status == 200:
        supabase_data = json.loads(verify_response.read().decode())
        if supabase_data and len(supabase_data) > 0:
            raw = supabase_data[0]['raw_data']
            has_trade = 'trade' in raw
            print(f"✅ Verification: Supabase now has trade object: {has_trade}")
            if has_trade:
                print(f"   Buy price: ${raw['trade']['buyPrice']}")
        else:
            print("❌ Could not find updated record")
except Exception as e:
    print(f"❌ Verification failed: {e}")