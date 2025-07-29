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

KROM_API_TOKEN = env_vars['KROM_API_TOKEN']

print("=== Checking KROM API Response Structure ===")
print(f"Time: {datetime.now()}\n")

# Fetch the latest 100 from KROM API
url = "https://krom.one/api/v1/calls"

req = urllib.request.Request(url)
req.add_header('Authorization', f'Bearer {KROM_API_TOKEN}')

try:
    response = urllib.request.urlopen(req)
    calls = json.loads(response.read().decode())
    
    print(f"Fetched {len(calls)} calls from KROM API\n")
    
    # Analyze the structure
    has_trade_section = 0
    no_trade_section = 0
    
    # Categories
    with_buy_price = []
    with_trade_but_no_price = []
    no_trade_at_all = []
    
    for call in calls:
        ticker = call.get('token', {}).get('symbol', 'Unknown')
        call_id = call.get('_id', 'Unknown')
        
        if 'trade' in call:
            has_trade_section += 1
            trade = call['trade']
            
            if 'buyPrice' in trade:
                with_buy_price.append({
                    'ticker': ticker,
                    'buyPrice': trade['buyPrice'],
                    'buyTimestamp': trade.get('buyTimestamp'),
                    'roi': trade.get('roi'),
                    'error': trade.get('error', False)
                })
            else:
                with_trade_but_no_price.append({
                    'ticker': ticker,
                    'trade_keys': list(trade.keys())
                })
        else:
            no_trade_section += 1
            no_trade_at_all.append(ticker)
    
    # Print summary
    print("=== Summary ===")
    print(f"Total calls: {len(calls)}")
    print(f"- Have 'trade' section: {has_trade_section}")
    print(f"  - With buyPrice: {len(with_buy_price)}")
    print(f"  - Without buyPrice: {len(with_trade_but_no_price)}")
    print(f"- No 'trade' section at all: {no_trade_section}")
    
    # Show examples
    print(f"\n=== Calls WITH trade section and buyPrice ({len(with_buy_price)}) ===")
    for item in with_buy_price[:3]:
        print(f"- {item['ticker']}: buyPrice=${item['buyPrice']}, roi={item['roi']}")
    
    print(f"\n=== Calls WITH trade section but NO buyPrice ({len(with_trade_but_no_price)}) ===")
    for item in with_trade_but_no_price[:5]:
        print(f"- {item['ticker']}: trade keys = {item['trade_keys']}")
    
    print(f"\n=== Calls with NO trade section at all ({no_trade_section}) ===")
    if no_trade_at_all:
        print(f"Examples: {', '.join(no_trade_at_all[:20])}")
        if len(no_trade_at_all) > 20:
            print(f"... and {len(no_trade_at_all) - 20} more")
    
    # Look at a full example of each type
    print("\n=== Full Examples ===")
    
    # Find one with trade and buyPrice
    for call in calls:
        if 'trade' in call and 'buyPrice' in call['trade']:
            print(f"\n1. Call WITH trade and buyPrice ({call.get('token', {}).get('symbol', 'Unknown')}):")
            print(json.dumps(call['trade'], indent=2))
            break
    
    # Find one with trade but no buyPrice
    for call in calls:
        if 'trade' in call and 'buyPrice' not in call['trade']:
            print(f"\n2. Call WITH trade but NO buyPrice ({call.get('token', {}).get('symbol', 'Unknown')}):")
            print(json.dumps(call['trade'], indent=2))
            break
    
    # Find one with no trade
    for call in calls:
        if 'trade' not in call:
            ticker = call.get('token', {}).get('symbol', 'Unknown')
            print(f"\n3. Call with NO trade section ({ticker}):")
            print("Top-level keys:", list(call.keys()))
            break
            
except Exception as e:
    print(f"Error: {e}")