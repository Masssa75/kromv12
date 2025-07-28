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

# Get multiple calls with pool_address to test
url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
url += "?select=krom_id,ticker,raw_data,pool_address,contract_address"
url += "&pool_address=not.is.null"
url += "&raw_data->trade->buyPrice=not.is.null"
url += "&limit=5"

req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)

try:
    response = urllib.request.urlopen(req)
    calls = json.loads(response.read().decode())
    
    print("=== Testing Price Matching with Pool Addresses ===\n")
    
    results = []
    
    for call in calls:
        ticker = call['ticker']
        krom_price = float(call['raw_data']['trade']['buyPrice'])
        timestamp = call['raw_data']['timestamp']
        
        print(f"Testing {ticker}...")
        
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
        
        try:
            edge_response = urllib.request.urlopen(edge_req)
            result = json.loads(edge_response.read().decode())
            
            if result.get('priceAtCall'):
                edge_price = float(result['priceAtCall'])
                diff_pct = abs(krom_price - edge_price) / krom_price * 100
                
                results.append({
                    'ticker': ticker,
                    'krom_price': krom_price,
                    'edge_price': edge_price,
                    'diff_pct': diff_pct,
                    'match': diff_pct < 5
                })
            else:
                results.append({
                    'ticker': ticker,
                    'krom_price': krom_price,
                    'edge_price': None,
                    'diff_pct': None,
                    'match': False
                })
        except Exception as e:
            print(f"  Error: {e}")
            results.append({
                'ticker': ticker,
                'krom_price': krom_price,
                'edge_price': None,
                'diff_pct': None,
                'match': False
            })
    
    # Summary
    print("\n=== SUMMARY ===")
    print(f"{'Token':<10} {'KROM Price':<15} {'Edge Price':<15} {'Diff %':<10} {'Match?'}")
    print("-" * 65)
    
    matches = 0
    for r in results:
        edge_str = f"${r['edge_price']:.8f}" if r['edge_price'] else "N/A"
        diff_str = f"{r['diff_pct']:.2f}%" if r['diff_pct'] is not None else "N/A"
        match_str = "✅" if r['match'] else "❌"
        
        print(f"{r['ticker']:<10} ${r['krom_price']:<14.8f} {edge_str:<15} {diff_str:<10} {match_str}")
        
        if r['match']:
            matches += 1
    
    print(f"\nMatches: {matches}/{len(results)} ({matches/len(results)*100:.0f}%)")
    
except Exception as e:
    print(f"Error: {e}")