import json
import urllib.request
import urllib.error
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
KROM_API_TOKEN = env_vars['KROM_API_TOKEN']

def fetch_krom_api(limit=100):
    """Fetch latest calls from KROM API"""
    url = f"https://krom.one/api/v1/calls?limit={limit}"
    
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {KROM_API_TOKEN}')
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        # KROM API returns array directly, not wrapped in 'data'
        if isinstance(data, list):
            return data
        return data.get('data', [])
    except Exception as e:
        print(f"Error fetching from KROM: {e}")
        return []

def update_call_in_supabase(krom_call):
    """Update a single call with complete raw_data"""
    krom_id = krom_call.get('id')
    if not krom_id:
        return False
    
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls?krom_id=eq.{krom_id}"
    
    update_data = {
        "raw_data": krom_call
    }
    
    data = json.dumps(update_data).encode('utf-8')
    
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
        print(f"Error updating {krom_id}: {e}")
        return False

def get_calls_without_trade_data(limit=100, offset=0):
    """Get calls from Supabase that don't have trade data"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += f"?select=krom_id,ticker,raw_data"
    url += f"&order=created_at.desc"
    url += f"&limit={limit}"
    url += f"&offset={offset}"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        all_calls = json.loads(response.read().decode())
        
        # Filter for calls without trade section
        return [call for call in all_calls if not call.get('raw_data', {}).get('trade')]
    except Exception as e:
        print(f"Error fetching from Supabase: {e}")
        return []

print("=== Simple Raw Data Repopulation ===")
print(f"Started at: {datetime.now()}\n")

# First, let's try to update from the latest KROM API data
print("Fetching latest 100 calls from KROM API...")
krom_calls = fetch_krom_api(limit=100)
print(f"Fetched {len(krom_calls)} calls from KROM\n")

if krom_calls:
    # Check how many have trade data
    with_trade = sum(1 for c in krom_calls if 'trade' in c)
    print(f"{with_trade} out of {len(krom_calls)} have trade data\n")
    
    # Update each call
    updated = 0
    for i, krom_call in enumerate(krom_calls):
        krom_id = krom_call.get('id')
        ticker = krom_call.get('token', {}).get('symbol', 'Unknown')
        has_trade = 'trade' in krom_call
        
        if update_call_in_supabase(krom_call):
            updated += 1
            status = "✅ with trade" if has_trade else "✅ no trade"
            if has_trade:
                buy_price = krom_call['trade'].get('buyPrice', 'N/A')
                print(f"{i+1}. {status} {ticker} - buyPrice: {buy_price}")
            else:
                print(f"{i+1}. {status} {ticker}")
        else:
            print(f"{i+1}. ❌ Failed {ticker}")
        
        # Small delay to avoid rate limiting
        if i > 0 and i % 10 == 0:
            time.sleep(0.5)
    
    print(f"\nUpdated {updated} out of {len(krom_calls)} calls")
else:
    print("No data returned from KROM API")

# Now check how many still need updating
print("\n" + "="*50)
print("Checking database status...")

# Count calls without trade data
total_without_trade = 0
offset = 0
batch_size = 1000

while True:
    batch = get_calls_without_trade_data(limit=batch_size, offset=offset)
    if not batch:
        break
    total_without_trade += len(batch)
    offset += batch_size
    if offset >= 10000:  # Safety limit
        break

print(f"\nTotal calls without trade data: {total_without_trade:,}")
print(f"This represents approximately {total_without_trade/5636*100:.1f}% of all calls")

print(f"\nFinished at: {datetime.now()}")