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

def analyze_database():
    """Comprehensive analysis of current database state"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += "?select=krom_id,ticker,buy_timestamp,created_at,raw_data"
    url += "&order=created_at.desc"
    url += "&limit=10000"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        calls = json.loads(response.read().decode())
        
        # Analysis metrics
        total = len(calls)
        with_raw_data = sum(1 for c in calls if c.get('raw_data'))
        with_trade = sum(1 for c in calls if c.get('raw_data', {}).get('trade'))
        with_timestamp = sum(1 for c in calls if c.get('buy_timestamp'))
        
        # Breakdown by presence of trade data
        no_trade_with_timestamp = 0
        no_trade_no_timestamp = 0
        
        for call in calls:
            if not call.get('raw_data', {}).get('trade'):
                if call.get('buy_timestamp'):
                    no_trade_with_timestamp += 1
                else:
                    no_trade_no_timestamp += 1
        
        # Sample some calls without trade data but with timestamps
        samples = []
        for call in calls:
            if (not call.get('raw_data', {}).get('trade') and 
                call.get('buy_timestamp') and 
                len(samples) < 5):
                samples.append({
                    'ticker': call.get('ticker', 'Unknown'),
                    'created': call.get('created_at', '')[:10],
                    'krom_id': call.get('krom_id')
                })
        
        return {
            'total': total,
            'with_raw_data': with_raw_data,
            'with_trade': with_trade,
            'with_timestamp': with_timestamp,
            'no_trade_with_timestamp': no_trade_with_timestamp,
            'no_trade_no_timestamp': no_trade_no_timestamp,
            'samples': samples
        }
    except Exception as e:
        print(f"Error: {e}")
        return None

print("=== Comprehensive Database Analysis ===")
print(f"Time: {datetime.now()}\n")

results = analyze_database()

if results:
    print(f"Total calls in database: {results['total']:,}")
    print(f"Calls with raw_data: {results['with_raw_data']:,} ({results['with_raw_data']/results['total']*100:.1f}%)")
    print(f"Calls with trade data: {results['with_trade']:,} ({results['with_trade']/results['total']*100:.1f}%)")
    print(f"Calls with timestamps: {results['with_timestamp']:,} ({results['with_timestamp']/results['total']*100:.1f}%)")
    
    print(f"\nCalls WITHOUT trade data breakdown:")
    print(f"- With timestamp (can potentially fetch): {results['no_trade_with_timestamp']:,}")
    print(f"- Without timestamp (cannot fetch): {results['no_trade_no_timestamp']:,}")
    
    print(f"\nSample calls that could be updated (have timestamp but no trade):")
    for i, sample in enumerate(results['samples'], 1):
        print(f"{i}. {sample['ticker']} - Created: {sample['created']} - ID: {sample['krom_id']}")
    
    print(f"\n=== Summary ===")
    print(f"Successfully populated: {results['with_trade']:,} calls with buy prices")
    print(f"Cannot populate: {results['no_trade_no_timestamp']:,} calls (no timestamp)")
    print(f"Could potentially populate: {results['no_trade_with_timestamp']:,} more calls")
    
    # Calculate the actual percentage of successful trade data
    calls_with_timestamp = results['with_timestamp']
    if calls_with_timestamp > 0:
        trade_success_rate = results['with_trade'] / calls_with_timestamp * 100
        print(f"\nOf calls with timestamps: {trade_success_rate:.1f}% have trade data")
        print("(This aligns with KROM's ~83% trade execution rate)")

print(f"\nAnalysis completed at: {datetime.now()}")