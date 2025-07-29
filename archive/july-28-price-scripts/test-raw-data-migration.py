import sqlite3
import json
import os
import urllib.request
import urllib.parse
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

# Connect to SQLite
conn = sqlite3.connect('krom_calls.db')
cursor = conn.cursor()

# Get the 2 most recent calls with raw_data
cursor.execute('''
    SELECT id, symbol, raw_data, buy_timestamp
    FROM calls 
    WHERE raw_data IS NOT NULL
    ORDER BY buy_timestamp DESC
    LIMIT 2
''')

results = cursor.fetchall()

print(f"Found {len(results)} most recent calls to update\n")

for krom_id, symbol, raw_data_str, buy_timestamp in results:
    raw_data = json.loads(raw_data_str)
    
    print(f"Token: {symbol}")
    print(f"Krom ID: {krom_id}")
    print(f"Buy timestamp: {datetime.fromtimestamp(buy_timestamp)}")
    print(f"Raw data has trade object: {'trade' in raw_data}")
    
    if 'trade' in raw_data:
        print(f"  Buy price: ${raw_data['trade']['buyPrice']}")
        print(f"  ROI: {raw_data['trade']['roi']}")
    
    # Update Supabase
    print(f"\nUpdating Supabase raw_data...")
    
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls?krom_id=eq.{krom_id}"
    
    # Update just the raw_data field
    data = json.dumps({
        "raw_data": raw_data
    }).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, method='PATCH')
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')
    req.add_header('Content-Type', 'application/json')
    req.add_header('Prefer', 'return=minimal')
    
    try:
        response = urllib.request.urlopen(req)
        if response.status == 204:
            print("✅ Successfully updated Supabase")
        else:
            print(f"❌ Failed to update: {response.status}")
    except urllib.error.HTTPError as e:
        print(f"❌ Failed to update: {e.code}")
        print(f"Response: {e.read().decode()}")
    
    # Verify the update
    print("\nVerifying update...")
    verify_url = f"{SUPABASE_URL}/rest/v1/crypto_calls?krom_id=eq.{krom_id}&select=raw_data"
    
    verify_req = urllib.request.Request(verify_url)
    verify_req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    verify_req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')
    
    try:
        verify_response = urllib.request.urlopen(verify_req)
        if verify_response.status == 200:
            supabase_data = json.loads(verify_response.read().decode())
            if supabase_data and len(supabase_data) > 0:
                supabase_raw = supabase_data[0]['raw_data']
                has_trade = 'trade' in supabase_raw
                print(f"✅ Verification: Supabase now has trade object: {has_trade}")
                if has_trade and 'buyPrice' in supabase_raw['trade']:
                    print(f"   Buy price in Supabase: ${supabase_raw['trade']['buyPrice']}")
            else:
                print("❌ Could not find updated record")
    except Exception as e:
        print(f"❌ Verification failed: {e}")
    
    print("-" * 60)

conn.close()
print("\nMigration test complete!")