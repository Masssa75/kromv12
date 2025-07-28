import json
import urllib.request
import os
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

# Hardcode the remaining krom_ids
remaining_ids = [
    "68850fd6eb25eec68caf0015",  # SOL
    "68801ae0eb25eec68cad8bfd",  # W
    "68801631eb25eec68cad8a6a",  # W
    "687d698ceb25eec68cacbe33",  # BILLY
    "687986e0eb25eec68cab9bad",  # XRP
    "68706537eb25eec68ca8db11",  # BTC
    "68672624eb25eec68ca6235c",  # APE
    "686406a4eb25eec68ca53b8b",  # MEW
    "68618efbeb25eec68ca481ca",  # SOL
    "686057fbeb25eec68ca42a02"   # INTERN
]

def clear_price_data(krom_id):
    """Clear all price-related fields for a specific call"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls?krom_id=eq.{krom_id}"
    
    # Set all price fields to null
    clear_data = {
        "price_at_call": None,
        "current_price": None,
        "ath_price": None,
        "ath_timestamp": None,
        "roi_percent": None,
        "ath_roi_percent": None,
        "market_cap_at_call": None,
        "current_market_cap": None,
        "ath_market_cap": None,
        "fdv_at_call": None,
        "current_fdv": None,
        "ath_fdv": None,
        "price_fetched_at": None,
        "price_network": None,
        "token_supply": None
    }
    
    data = json.dumps(clear_data).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, method='PATCH')
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')
    req.add_header('Content-Type', 'application/json')
    req.add_header('Prefer', 'return=representation')
    
    try:
        response = urllib.request.urlopen(req)
        if response.status == 200:
            return True
        return False
    except Exception as e:
        print(f"Error clearing {krom_id}: {e}")
        return False

def verify_no_price_data():
    """Verify no records have price data"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += f"?select=krom_id"
    url += f"&or=(price_at_call.not.is.null,current_price.not.is.null,ath_price.not.is.null)"
    url += f"&limit=1"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        return len(data) == 0
    except Exception as e:
        print(f"Error verifying: {e}")
        return False

print("=== Clear Final 10 Price Records ===")
print(f"Started at: {datetime.now()}\n")

print("These are the final records that were fetched today at 05:01 AM")
print("Clearing these 10 records...\n")

cleared = 0
failed = 0

for i, krom_id in enumerate(remaining_ids):
    print(f"{i+1}. Clearing {krom_id}...", end=" ")
    if clear_price_data(krom_id):
        print("✅ Success")
        cleared += 1
    else:
        print("❌ Failed")
        failed += 1

print(f"\n=== Summary ===")
print(f"Successfully cleared: {cleared}")
print(f"Failed: {failed}")

print("\nVerifying final state...")
if verify_no_price_data():
    print("✅ VERIFIED: No records with price data remaining!")
else:
    print("⚠️  Warning: Some records may still have price data")

print(f"\nFinished at: {datetime.now()}")