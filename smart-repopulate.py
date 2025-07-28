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
KROM_API_TOKEN = env_vars['KROM_API_TOKEN']

def get_oldest_call_without_trade():
    """Get the oldest call that doesn't have trade data"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += "?select=krom_id,ticker,buy_timestamp,raw_data"
    url += "&order=buy_timestamp.asc"
    url += "&limit=100"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        calls = json.loads(response.read().decode())
        
        # Find first call without trade data
        for call in calls:
            if call.get('raw_data') and 'trade' not in call['raw_data']:
                return call
        return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def fetch_krom_around_timestamp(timestamp, limit=100):
    """Fetch KROM calls around a specific timestamp"""
    # Add some buffer to ensure we get the call
    buffer_time = 3600  # 1 hour buffer
    url = f"https://krom.one/api/v1/calls?beforeTimestamp={timestamp + buffer_time}&limit={limit}"
    
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'Bearer {KROM_API_TOKEN}')
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        return data if isinstance(data, list) else []
    except Exception as e:
        print(f"KROM API error: {e}")
        return []

def update_if_has_trade(krom_call):
    """Update call in Supabase if it has trade data"""
    if 'trade' not in krom_call:
        return False, False
    
    krom_id = krom_call.get('id')
    if not krom_id:
        return False, False
    
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls?krom_id=eq.{krom_id}"
    data = json.dumps({"raw_data": krom_call}).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, method='PATCH')
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')
    req.add_header('Content-Type', 'application/json')
    
    try:
        response = urllib.request.urlopen(req)
        if response.status == 200:
            return True, True
        return False, False
    except Exception as e:
        print(f"Update error for {krom_id}: {e}")
        return False, False

print("=== Smart Repopulation - Target Calls Without Trade Data ===")
print(f"Started at: {datetime.now()}\n")

# Process calls one by one, targeting those without trade data
updated_count = 0
checked_count = 0
max_iterations = 50

for i in range(max_iterations):
    # Get oldest call without trade data
    target_call = get_oldest_call_without_trade()
    
    if not target_call:
        print("No more calls without trade data found!")
        break
    
    krom_id = target_call['krom_id']
    ticker = target_call.get('ticker', 'Unknown')
    timestamp = target_call.get('buy_timestamp')
    
    if not timestamp:
        print(f"Skip {ticker} - no timestamp")
        continue
    
    date_str = datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M')
    print(f"{i+1}. Checking {ticker} from {date_str}...", end=" ")
    
    # Fetch KROM data around this timestamp
    krom_calls = fetch_krom_around_timestamp(timestamp, limit=100)
    
    if not krom_calls:
        print("No KROM data")
        continue
    
    # Look for this specific call
    found = False
    for krom_call in krom_calls:
        if krom_call.get('id') == krom_id:
            found = True
            success, has_trade = update_if_has_trade(krom_call)
            if success:
                buy_price = krom_call['trade'].get('buyPrice', 'N/A')
                print(f"✅ Updated with trade (buyPrice: {buy_price})")
                updated_count += 1
            else:
                print(f"❌ No trade data in KROM")
            break
    
    if not found:
        print("Not found in batch")
    
    checked_count += 1
    
    # Progress report
    if checked_count % 10 == 0:
        print(f"\nProgress: Checked {checked_count}, Updated {updated_count}")
        print()
    
    # Rate limiting
    time.sleep(0.3)

print(f"\n{'='*60}")
print(f"=== Summary ===")
print(f"Calls checked: {checked_count}")
print(f"Calls updated with trade data: {updated_count}")
if checked_count > 0:
    print(f"Success rate: {updated_count/checked_count*100:.1f}%")
print(f"{'='*60}")

# Final status check
print("\nRunning final database check...")
import check_database_status

print(f"\nFinished at: {datetime.now()}")