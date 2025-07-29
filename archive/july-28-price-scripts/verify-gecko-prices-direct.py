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

# Get 10 oldest calls with KROM price and pool address
url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
url += "?select=krom_id,ticker,raw_data,pool_address,contract_address,created_at"
url += "&pool_address=not.is.null"
url += "&raw_data->trade->buyPrice=not.is.null"
url += "&order=created_at.asc"
url += "&limit=10"

req = urllib.request.Request(url)
req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)

try:
    response = urllib.request.urlopen(req)
    calls = json.loads(response.read().decode())
    
    print("=== Direct GeckoTerminal API Price Verification ===")
    print(f"Testing {len(calls)} oldest calls with KROM prices\n")
    
    matches = 0
    
    for idx, call in enumerate(calls, 1):
        ticker = call['ticker']
        krom_price = float(call['raw_data']['trade']['buyPrice'])
        timestamp = call['raw_data']['timestamp']
        pool = call['pool_address']
        network = call['raw_data']['token']['network']
        created_str = call['created_at'].replace('Z', '+00:00').split('.')[0] + '+00:00'
        created = datetime.fromisoformat(created_str)
        
        print(f"\n{idx}. {ticker} (Created: {created.strftime('%Y-%m-%d')})")
        print(f"   KROM Price: ${krom_price:.10f}")
        print(f"   Timestamp: {datetime.fromtimestamp(timestamp).isoformat()}")
        print(f"   Pool: {pool[:10]}...{pool[-10:]}")
        
        # Direct GeckoTerminal API call for minute candles
        gecko_url = f"https://api.geckoterminal.com/api/v2/networks/{network}/pools/{pool}/ohlcv/minute"
        gecko_url += f"?before_timestamp={timestamp + 300}&limit=10&currency=usd"
        
        try:
            gecko_response = urllib.request.urlopen(gecko_url)
            data = json.loads(gecko_response.read().decode())
            
            ohlcv_list = data['data']['attributes']['ohlcv_list']
            
            if ohlcv_list:
                # Find the candle that contains our timestamp
                found_match = False
                for candle in ohlcv_list:
                    candle_time = candle[0]
                    open_price = candle[1]
                    high_price = candle[2]
                    low_price = candle[3]
                    close_price = candle[4]
                    
                    # Check if KROM price falls within this candle's range
                    if low_price <= krom_price <= high_price:
                        time_diff = candle_time - timestamp
                        print(f"   ✅ MATCH FOUND! Candle at {datetime.fromtimestamp(candle_time).strftime('%H:%M:%S')} ({time_diff:+d}s)")
                        print(f"      Range: ${low_price:.10f} - ${high_price:.10f}")
                        print(f"      Open: ${open_price:.10f}, Close: ${close_price:.10f}")
                        
                        # Calculate how close KROM price is to the range
                        if krom_price == low_price:
                            print(f"      KROM price = Low price (perfect match!)")
                        elif krom_price == high_price:
                            print(f"      KROM price = High price (perfect match!)")
                        else:
                            position = (krom_price - low_price) / (high_price - low_price) * 100
                            print(f"      KROM price is {position:.1f}% up from low")
                        
                        found_match = True
                        matches += 1
                        break
                
                if not found_match:
                    # Show closest candle
                    closest = min(ohlcv_list, key=lambda x: abs(x[0] - timestamp))
                    print(f"   ❌ No match. Closest candle: ${closest[3]:.10f} - ${closest[2]:.10f}")
                    print(f"      KROM price outside all candle ranges")
                    
            else:
                print(f"   ⚠️  No OHLCV data available")
                
        except Exception as e:
            print(f"   ❌ Error fetching data: {e}")
    
    print(f"\n{'='*60}")
    print(f"Summary: {matches}/{len(calls)} prices matched within minute candles")
    print(f"Match rate: {matches/len(calls)*100:.0f}%")
    print(f"{'='*60}")
    
except Exception as e:
    print(f"Error: {e}")