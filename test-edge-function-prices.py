import json
import urllib.request
from datetime import datetime
import time

# Load environment variables
env_vars = {}
with open('.env', 'r') as f:
    for line in f:
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.strip().split('=', 1)
            env_vars[k] = v.strip()

SUPABASE_URL = env_vars['SUPABASE_URL']
SUPABASE_SERVICE_ROLE_KEY = env_vars['SUPABASE_SERVICE_ROLE_KEY']

# Get 5 calls with KROM price and pool address
url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
url += "?select=krom_id,ticker,raw_data,pool_address,contract_address,created_at"
url += "&pool_address=not.is.null"
url += "&raw_data->trade->buyPrice=not.is.null"
url += "&order=created_at.asc"
url += "&limit=5"

req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)

try:
    response = urllib.request.urlopen(req)
    calls = json.loads(response.read().decode())
    
    print("=== Testing Edge Function with Pool Addresses ===")
    print(f"Testing {len(calls)} calls with KROM prices\n")
    
    results = []
    
    for idx, call in enumerate(calls, 1):
        ticker = call['ticker']
        krom_price = float(call['raw_data']['trade']['buyPrice'])
        timestamp = call['raw_data']['timestamp']
        pool = call['pool_address']
        network = call['raw_data']['token']['network']
        contract = call['contract_address']
        
        print(f"\n{idx}. {ticker}")
        print(f"   KROM Price: ${krom_price:.10f}")
        print(f"   Pool: {pool}")
        
        # Call edge function with pool address
        edge_url = f"{SUPABASE_URL}/functions/v1/crypto-price-single"
        
        data = json.dumps({
            "contractAddress": contract,
            "callTimestamp": timestamp,
            "network": network,
            "poolAddress": pool
        }).encode('utf-8')
        
        edge_req = urllib.request.Request(edge_url, data=data, method='POST')
        edge_req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
        edge_req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')
        edge_req.add_header('Content-Type', 'application/json')
        
        try:
            edge_response = urllib.request.urlopen(edge_req)
            result = json.loads(edge_response.read().decode())
            
            if result.get('priceAtCall'):
                edge_price = float(result['priceAtCall'])
                diff_pct = abs(krom_price - edge_price) / krom_price * 100
                
                print(f"   Edge Price: ${edge_price:.10f}")
                print(f"   Difference: {diff_pct:.2f}%")
                
                if diff_pct < 5:
                    print(f"   ✅ Prices match within 5%!")
                else:
                    print(f"   ❌ Price mismatch > 5%")
                
                results.append({
                    'ticker': ticker,
                    'match': diff_pct < 5,
                    'diff_pct': diff_pct
                })
            else:
                print(f"   ⚠️  No historical price returned")
                results.append({
                    'ticker': ticker,
                    'match': False,
                    'diff_pct': None
                })
                
        except Exception as e:
            print(f"   ❌ Edge function error: {e}")
            results.append({
                'ticker': ticker,
                'match': False,
                'diff_pct': None
            })
        
        # Small delay to avoid rate limiting
        time.sleep(0.5)
    
    # Summary
    matches = sum(1 for r in results if r['match'])
    print(f"\n{'='*60}")
    print(f"Summary: {matches}/{len(results)} prices matched")
    print(f"Match rate: {matches/len(results)*100:.0f}%")
    
    # Show details
    print(f"\nDetails:")
    for r in results:
        if r['diff_pct'] is not None:
            print(f"  {r['ticker']}: {r['diff_pct']:.2f}% difference")
        else:
            print(f"  {r['ticker']}: No price data")
    
except Exception as e:
    print(f"Error: {e}")