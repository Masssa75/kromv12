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

def get_calls_without_trade_data():
    """Get detailed info about calls without trade data"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += f"?select=krom_id,ticker,created_at,buy_timestamp,raw_data,price_at_call,current_price,roi_percent"
    url += f"&raw_data->>trade=is.null"
    url += f"&order=created_at.desc"
    url += f"&limit=100"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching calls: {e}")
        return []

print("=== Analyzing Calls Without Trade Data ===")
print(f"Time: {datetime.now()}\n")

# Get calls without trade data
calls = get_calls_without_trade_data()
print(f"Found {len(calls)} calls without trade data in raw_data\n")

# Categorize the calls
has_raw_data = 0
no_raw_data = 0
has_price_data = 0
has_buy_timestamp = 0
completely_empty = 0

# Detailed analysis
categories = {
    'has_complete_raw_data': [],
    'has_partial_raw_data': [],
    'no_raw_data_at_all': [],
    'has_fetched_prices': [],
    'completely_empty': []
}

for call in calls:
    ticker = call['ticker']
    krom_id = call['krom_id']
    raw_data = call.get('raw_data')
    
    # Check what data exists
    has_raw = bool(raw_data)
    has_price = call.get('price_at_call') is not None
    has_roi = call.get('roi_percent') is not None
    has_buy_ts = call.get('buy_timestamp') is not None
    
    if has_raw:
        has_raw_data += 1
        # Check if it's complete (has token info, etc)
        if raw_data.get('token') and raw_data.get('timestamp'):
            categories['has_complete_raw_data'].append({
                'ticker': ticker,
                'has_token_info': bool(raw_data.get('token')),
                'has_message': bool(raw_data.get('text')),
                'has_group': bool(raw_data.get('group')),
                'timestamp': raw_data.get('timestamp')
            })
        else:
            categories['has_partial_raw_data'].append({
                'ticker': ticker,
                'raw_data_keys': list(raw_data.keys()) if raw_data else []
            })
    else:
        no_raw_data += 1
        categories['no_raw_data_at_all'].append(ticker)
    
    if has_price or has_roi:
        has_price_data += 1
        categories['has_fetched_prices'].append({
            'ticker': ticker,
            'price_at_call': call.get('price_at_call'),
            'current_price': call.get('current_price'),
            'roi': call.get('roi_percent')
        })
    
    if has_buy_ts:
        has_buy_timestamp += 1
    
    if not has_raw and not has_price and not has_buy_ts:
        completely_empty += 1
        categories['completely_empty'].append(ticker)

# Print summary
print("=== Summary ===")
print(f"Total calls without trade data: {len(calls)}")
print(f"- Have raw_data (but no trade): {has_raw_data}")
print(f"- No raw_data at all: {no_raw_data}")
print(f"- Have fetched price data: {has_price_data}")
print(f"- Have buy_timestamp: {has_buy_timestamp}")
print(f"- Completely empty: {completely_empty}")

# Show details for each category
print(f"\n=== Calls with Complete raw_data (but no trade) ===")
print(f"Count: {len(categories['has_complete_raw_data'])}")
if categories['has_complete_raw_data']:
    for item in categories['has_complete_raw_data'][:5]:
        print(f"  - {item['ticker']}: has token info, message, timestamp")
        if item['timestamp']:
            dt = datetime.fromtimestamp(item['timestamp'])
            print(f"    Timestamp: {dt}")

print(f"\n=== Calls with Partial raw_data ===")
print(f"Count: {len(categories['has_partial_raw_data'])}")
if categories['has_partial_raw_data']:
    for item in categories['has_partial_raw_data'][:5]:
        print(f"  - {item['ticker']}: keys = {item['raw_data_keys']}")

print(f"\n=== Calls with NO raw_data ===")
print(f"Count: {len(categories['no_raw_data_at_all'])}")
if categories['no_raw_data_at_all']:
    print(f"Examples: {', '.join(categories['no_raw_data_at_all'][:10])}")

print(f"\n=== Calls with Fetched Prices (but no trade data) ===")
print(f"Count: {len(categories['has_fetched_prices'])}")
if categories['has_fetched_prices']:
    for item in categories['has_fetched_prices'][:5]:
        print(f"  - {item['ticker']}: Entry ${item['price_at_call']}, Current ${item['current_price']}, ROI {item['roi']}%")

print(f"\n=== Completely Empty Calls ===")
print(f"Count: {len(categories['completely_empty'])}")
if categories['completely_empty']:
    print(f"Examples: {', '.join(categories['completely_empty'][:10])}")

# Check if we just updated some of these
print(f"\n=== Recent Updates Check ===")
recently_updated = [c for c in calls if c.get('raw_data') and not c['raw_data'].get('trade')]
print(f"Calls with raw_data but no trade: {len(recently_updated)}")
if recently_updated:
    print("These were likely just updated from KROM API but don't have trade data there either")
    for call in recently_updated[:5]:
        print(f"  - {call['ticker']}: Has raw_data but no trade object")