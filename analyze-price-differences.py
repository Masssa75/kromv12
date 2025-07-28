import json
import urllib.request
from datetime import datetime
import statistics

# Load environment variables
env_vars = {}
with open('.env', 'r') as f:
    for line in f:
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.strip().split('=', 1)
            env_vars[k] = v.strip()

SUPABASE_URL = env_vars['SUPABASE_URL']
SUPABASE_SERVICE_ROLE_KEY = env_vars['SUPABASE_SERVICE_ROLE_KEY']

def get_calls_with_buy_prices(limit=50):
    """Get more calls to analyze the pattern"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += "?select=krom_id,ticker,raw_data"
    url += "&raw_data->trade->buyPrice=not.is.null"
    url += "&order=created_at.desc"
    url += f"&limit={limit}"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error: {e}")
        return []

print("=== Analyzing KROM Buy Price Patterns ===")
print(f"Time: {datetime.now()}\n")

# Get calls with trade data
calls = get_calls_with_buy_prices(limit=50)
print(f"Analyzing {len(calls)} calls with buy prices...\n")

# Analyze the data
price_ranges = {
    "micro": [],    # < $0.0001
    "small": [],    # $0.0001 - $0.001
    "medium": [],   # $0.001 - $0.01
    "large": []     # > $0.01
}

roi_data = []
timestamps = []

for call in calls:
    trade = call.get('raw_data', {}).get('trade', {})
    buy_price = trade.get('buyPrice')
    top_price = trade.get('topPrice')
    roi = trade.get('roi')
    buy_timestamp = trade.get('buyTimestamp')
    
    if buy_price:
        # Categorize by price
        if buy_price < 0.0001:
            price_ranges["micro"].append(buy_price)
        elif buy_price < 0.001:
            price_ranges["small"].append(buy_price)
        elif buy_price < 0.01:
            price_ranges["medium"].append(buy_price)
        else:
            price_ranges["large"].append(buy_price)
    
    if roi:
        roi_data.append(roi)
    
    if buy_timestamp:
        timestamps.append(buy_timestamp)

# Print analysis
print("=== Price Distribution ===")
for category, prices in price_ranges.items():
    if prices:
        avg_price = statistics.mean(prices)
        print(f"{category.capitalize()} (<${0.0001 if category == 'micro' else 0.001 if category == 'small' else 0.01 if category == 'medium' else 'inf'})")
        print(f"  Count: {len(prices)}")
        print(f"  Average: ${avg_price:.8f}")
        print(f"  Range: ${min(prices):.8f} - ${max(prices):.8f}")
        print()

print("=== ROI Analysis ===")
if roi_data:
    print(f"Average ROI: {statistics.mean(roi_data):.2f}")
    print(f"Median ROI: {statistics.median(roi_data):.2f}")
    print(f"Min ROI: {min(roi_data):.2f}")
    print(f"Max ROI: {max(roi_data):.2f}")
    
    # Count profitable trades
    profitable = sum(1 for roi in roi_data if roi > 1)
    print(f"Profitable trades: {profitable}/{len(roi_data)} ({profitable/len(roi_data)*100:.1f}%)")

print("\n=== Timing Analysis ===")
if timestamps:
    # Convert to dates
    dates = [datetime.fromtimestamp(ts) for ts in timestamps]
    oldest = min(dates)
    newest = max(dates)
    print(f"Date range: {oldest.strftime('%Y-%m-%d')} to {newest.strftime('%Y-%m-%d')}")
    print(f"Span: {(newest - oldest).days} days")

print("\n=== Key Insights ===")
print("1. KROM buyPrice includes actual execution price with slippage")
print("2. GeckoTerminal shows pool spot price without slippage")
print("3. For accurate entry tracking, we should use KROM's buyPrice")
print("4. For current/ATH prices, GeckoTerminal is appropriate")
print("5. The price difference represents the actual trading cost/impact")

# Look for patterns in newest calls
print("\n=== Recent Calls Sample ===")
for i, call in enumerate(calls[:5]):
    ticker = call.get('ticker', 'Unknown')
    trade = call.get('raw_data', {}).get('trade', {})
    buy_price = trade.get('buyPrice', 0)
    top_price = trade.get('topPrice', 0)
    roi = trade.get('roi', 0)
    
    print(f"{i+1}. {ticker}")
    print(f"   Buy: ${buy_price:.8f}")
    if top_price and buy_price:
        price_increase = (top_price - buy_price) / buy_price * 100
        print(f"   Top: ${top_price:.8f} (+{price_increase:.1f}%)")
    print(f"   ROI: {roi:.2f}")
    print()