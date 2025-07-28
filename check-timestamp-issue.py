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

print("=== Investigating Timestamp Issues ===")
print(f"Date: {datetime.now()}")

# Get a sample of calls that were marked as "No timestamp"
url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
url += f"?select=krom_id,buy_timestamp,created_at,raw_data"
url += f"&limit=10"
url += f"&order=created_at.asc"

req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)

response = urllib.request.urlopen(req)
sample_calls = json.loads(response.read().decode())

print(f"Examining {len(sample_calls)} sample calls...")

for i, call in enumerate(sample_calls):
    krom_id = call['krom_id']
    buy_timestamp = call.get('buy_timestamp')
    created_at = call.get('created_at')
    raw_data = call.get('raw_data', {})
    
    print(f"\n{i+1}. {krom_id[:8]}...")
    print(f"   buy_timestamp: {buy_timestamp}")
    print(f"   created_at: {created_at}")
    
    # Check what's in raw_data.trade
    trade = raw_data.get('trade', {})
    print(f"   raw_data.trade keys: {list(trade.keys())}")
    
    if 'buyTimestamp' in trade:
        print(f"   raw_data.trade.buyTimestamp: {trade['buyTimestamp']}")
    
    if 'buyPrice' in trade:
        print(f"   raw_data.trade.buyPrice: {trade['buyPrice']}")
    
    # Show what timestamp we could use
    if buy_timestamp:
        buy_ts = datetime.fromisoformat(buy_timestamp.replace('Z', '+00:00'))
        print(f"   ✅ Can use buy_timestamp: {buy_ts}")
    elif created_at:
        created_ts = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        print(f"   🔄 Can use created_at fallback: {created_ts}")
    else:
        print(f"   ❌ No usable timestamp")

print(f"\n{'='*60}")
print(f"ANALYSIS:")
print(f"We should update the populate script to:")
print(f"1. First try buy_timestamp")
print(f"2. Fall back to created_at if buy_timestamp is missing")
print(f"3. Only skip if both are missing")

print(f"\nThis should recover most of those 157 'No timestamp' records!")