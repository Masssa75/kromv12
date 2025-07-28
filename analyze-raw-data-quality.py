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

def get_sample_raw_data():
    """Get a sample of raw_data to analyze structure"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += "?select=krom_id,ticker,created_at,raw_data"
    url += "&order=created_at.desc"
    url += "&limit=20"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching: {e}")
        return []

print("=== Analyzing Raw Data Quality ===")
print(f"Time: {datetime.now()}\n")

# Get sample data
sample = get_sample_raw_data()

print("Checking structure of raw_data for newest 20 calls:\n")

for i, call in enumerate(sample[:10]):
    krom_id = call.get('krom_id', 'Unknown')
    ticker = call.get('ticker', 'Unknown')
    created = call.get('created_at', 'Unknown')[:10]
    raw_data = call.get('raw_data', {})
    
    print(f"{i+1}. {ticker} ({created}) - ID: {krom_id}")
    
    if not raw_data:
        print("   ❌ No raw_data")
    else:
        # Check what fields are present
        fields = list(raw_data.keys())
        print(f"   Fields present: {', '.join(fields[:5])}")
        if len(fields) > 5:
            print(f"   ... and {len(fields) - 5} more fields")
        
        # Check for trade section
        if 'trade' in raw_data:
            trade = raw_data['trade']
            buy_price = trade.get('buyPrice', 'N/A')
            print(f"   ✅ Has trade section - buyPrice: {buy_price}")
        else:
            print(f"   ❌ No trade section")
        
        # Check if it's just basic call info
        if 'callerUsername' in raw_data or 'message' in raw_data:
            print(f"   📝 Has call info: {raw_data.get('callerUsername', 'N/A')}")
        
        # Check token info
        if 'token' in raw_data:
            token = raw_data['token']
            ca = token.get('ca', 'N/A')
            print(f"   🪙 Has token info - CA: {ca[:10]}...")
    
    print()

# Let's check one with trade data specifically
print("\nLooking for a call WITH trade data...")
url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
url += "?select=krom_id,ticker,raw_data"
url += "&raw_data->trade=not.is.null"
url += "&limit=1"

req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)

try:
    response = urllib.request.urlopen(req)
    data = json.loads(response.read().decode())
    if data:
        call = data[0]
        print(f"Found: {call.get('ticker')} - ID: {call.get('krom_id')}")
        trade = call.get('raw_data', {}).get('trade', {})
        print(f"Trade data: {json.dumps(trade, indent=2)[:200]}...")
except Exception as e:
    print(f"Error: {e}")