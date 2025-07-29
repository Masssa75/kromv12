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

def count_total_calls():
    """Count total number of calls in database"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=krom_id"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    req.add_header('Range', '0-10000')
    req.add_header('Prefer', 'count=exact')
    
    try:
        response = urllib.request.urlopen(req)
        content_range = response.headers.get('content-range')
        if content_range:
            total = int(content_range.split('/')[-1])
            return total
        return 0
    except Exception as e:
        print(f"Error counting: {e}")
        return 0

def count_calls_with_raw_data():
    """Count calls that have raw_data"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=krom_id&raw_data=not.is.null"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    req.add_header('Range', '0-10000')
    req.add_header('Prefer', 'count=exact')
    
    try:
        response = urllib.request.urlopen(req)
        content_range = response.headers.get('content-range')
        if content_range:
            total = int(content_range.split('/')[-1])
            return total
        return 0
    except Exception as e:
        print(f"Error counting: {e}")
        return 0

def count_calls_with_trade_data():
    """Count calls that have raw_data with trade section"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=raw_data&raw_data=not.is.null&limit=1000"
    
    all_calls = []
    offset = 0
    
    while True:
        req = urllib.request.Request(f"{url}&offset={offset}")
        req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
        
        try:
            response = urllib.request.urlopen(req)
            data = json.loads(response.read().decode())
            if not data:
                break
            all_calls.extend(data)
            offset += 1000
        except Exception as e:
            print(f"Error fetching: {e}")
            break
    
    # Count how many have trade data
    with_trade = 0
    for call in all_calls:
        if call.get('raw_data', {}).get('trade'):
            with_trade += 1
    
    return with_trade, len(all_calls)

def get_sample_calls_without_raw_data():
    """Get sample of calls without raw_data"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += "?select=krom_id,ticker,created_at,raw_data"
    url += "&raw_data=is.null"
    url += "&order=created_at.desc"
    url += "&limit=10"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching: {e}")
        return []

print("=== Database Status Check ===")
print(f"Time: {datetime.now()}\n")

# Count total calls
total_calls = count_total_calls()
print(f"Total calls in database: {total_calls:,}")

# Count calls with raw_data
with_raw_data = count_calls_with_raw_data()
without_raw_data = total_calls - with_raw_data
print(f"Calls WITH raw_data: {with_raw_data:,} ({with_raw_data/total_calls*100:.1f}%)")
print(f"Calls WITHOUT raw_data: {without_raw_data:,} ({without_raw_data/total_calls*100:.1f}%)")

# Count calls with trade data
print("\nAnalyzing trade data in raw_data...")
with_trade, total_checked = count_calls_with_trade_data()
print(f"Calls with trade section: {with_trade:,} out of {total_checked:,} with raw_data ({with_trade/total_checked*100:.1f}%)")
print(f"Calls without trade section: {total_checked - with_trade:,} ({(total_checked - with_trade)/total_checked*100:.1f}%)")

# Show sample of calls without raw_data
print("\nSample of calls WITHOUT raw_data (newest first):")
sample = get_sample_calls_without_raw_data()
for i, call in enumerate(sample[:5]):
    print(f"{i+1}. {call.get('ticker', 'Unknown')} - {call.get('created_at', 'Unknown')[:10]} - ID: {call.get('krom_id', 'Unknown')}")

print(f"\n=== Summary ===")
print(f"Need to fetch raw_data for: {without_raw_data:,} calls")
print(f"Already have trade data for: {with_trade:,} calls (can use buyPrice immediately)")