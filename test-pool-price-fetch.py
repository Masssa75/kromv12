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

# Get a call with pool_address to test
url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
url += "?select=krom_id,ticker,raw_data,pool_address,contract_address,buy_timestamp"
url += "&pool_address=not.is.null"
url += "&raw_data->trade->buyPrice=not.is.null"
url += "&limit=1"

req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)

try:
    response = urllib.request.urlopen(req)
    calls = json.loads(response.read().decode())
    
    if calls:
        call = calls[0]
        print(f"Testing with {call['ticker']} (ID: {call['krom_id']})")
        print(f"Contract: {call['contract_address']}")
        print(f"Pool: {call['pool_address']}")
        print(f"KROM Buy Price: ${call['raw_data']['trade']['buyPrice']}")
        
        # Convert timestamp to seconds
        timestamp = call['raw_data']['timestamp']
        
        # Test the edge function
        edge_url = f"{SUPABASE_URL}/functions/v1/crypto-price-single"
        
        data = json.dumps({
            "contractAddress": call['contract_address'],
            "callTimestamp": timestamp,
            "network": call['raw_data']['token']['network'],
            "poolAddress": call['pool_address']
        }).encode('utf-8')
        
        edge_req = urllib.request.Request(edge_url, data=data, method='POST')
        edge_req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
        edge_req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')
        edge_req.add_header('Content-Type', 'application/json')
        
        edge_response = urllib.request.urlopen(edge_req)
        result = json.loads(edge_response.read().decode())
        
        print("\nEdge Function Response:")
        print(f"Price at call: ${result.get('priceAtCall')}")
        print(f"Current price: ${result.get('currentPrice')}")
        print(f"ROI: {result.get('roi')}%")
        
        # Compare prices
        if result.get('priceAtCall'):
            krom_price = float(call['raw_data']['trade']['buyPrice'])
            edge_price = float(result['priceAtCall'])
            diff_pct = abs(krom_price - edge_price) / krom_price * 100
            print(f"\nPrice comparison:")
            print(f"KROM price: ${krom_price}")
            print(f"Edge price: ${edge_price}")
            print(f"Difference: {diff_pct:.2f}%")
            
            if diff_pct < 5:
                print("✅ Prices match within 5% - using correct pool!")
            else:
                print("❌ Price mismatch > 5% - investigate further")
        
except Exception as e:
    print(f"Error: {e}")