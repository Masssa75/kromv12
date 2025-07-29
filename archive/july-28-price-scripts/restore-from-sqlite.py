import sqlite3
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

# Connect to SQLite database
conn = sqlite3.connect('krom_calls.db')
cursor = conn.cursor()

# IDs to restore
ids_to_restore = [
    ('REMI', '6886d413eb25eec68caf837f'),
    ('SLOP', '6886d2cbeb25eec68caf82f3'),
    ('QUOKKA', '6886c482eb25eec68caf7e75'),
    ('SPURDO', '6886bc02eb25eec68caf7bf5'),
    ('NYAN', '6886a784eb25eec68caf75aa')  # Also try the one that failed
]

print("Restoring correct data from SQLite backup...\n")

for ticker, krom_id in ids_to_restore:
    # Query SQLite for this specific ID
    cursor.execute("SELECT raw_data FROM calls WHERE krom_id = ?", (krom_id,))
    result = cursor.fetchone()
    
    if result and result[0]:
        try:
            raw_data = json.loads(result[0])
            
            # Verify it's the correct token
            db_ticker = raw_data.get('token', {}).get('symbol', 'Unknown')
            
            print(f"{ticker} (ID: {krom_id}):")
            print(f"  - Found in SQLite: {db_ticker}")
            
            if 'trade' in raw_data:
                print(f"  - Has trade data: Buy price ${raw_data['trade'].get('buyPrice', 'N/A')}")
            else:
                print(f"  - No trade data in SQLite")
            
            # Update Supabase with correct data
            url = f"{SUPABASE_URL}/rest/v1/crypto_calls?krom_id=eq.{krom_id}"
            
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
                    print(f"  ✅ Restored correct data")
                else:
                    print(f"  ❌ Failed to update: {response.status}")
            except Exception as e:
                print(f"  ❌ Error updating: {e}")
                
        except json.JSONDecodeError:
            print(f"{ticker}: ❌ Invalid JSON in SQLite")
    else:
        print(f"{ticker}: ❌ Not found in SQLite")
    
    print()

conn.close()
print("✅ Restoration completed.")