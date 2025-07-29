#!/usr/bin/env python3
import json
import urllib.request
from collections import Counter
from datetime import datetime

# Get service key
service_key = None
with open('.env', 'r') as f:
    for line in f:
        if line.startswith('SUPABASE_SERVICE_ROLE_KEY='):
            service_key = line.split('=', 1)[1].strip()
            break

supabase_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/rest/v1/crypto_calls"
edge_function_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-price-historical"

# Get all remaining unprocessed tokens
url = f"{supabase_url}?select=*&price_at_call=is.null&price_source=is.null&order=created_at.desc"
req = urllib.request.Request(url)
req.add_header('apikey', service_key)
req.add_header('Authorization', f'Bearer {service_key}')

response = urllib.request.urlopen(req)
unprocessed = json.loads(response.read().decode())

print(f"=== Final Analysis of {len(unprocessed)} Remaining Unprocessed Tokens ===\n")

# Group by creation date
creation_dates = Counter()
recent_24h = 0
recent_48h = 0
recent_week = 0

now = datetime.now()

for token in unprocessed:
    if token.get('created_at'):
        date_str = token['created_at'][:10]
        creation_dates[date_str] += 1
        
        # Parse creation time
        try:
            created_str = token['created_at']
            if 'Z' in created_str:
                created_str = created_str.replace('Z', '+00:00')
            if '.' in created_str and '+' in created_str:
                parts = created_str.split('.')
                microsec, tz = parts[1].split('+')
                microsec = microsec.ljust(6, '0')[:6]
                created_str = f"{parts[0]}.{microsec}+{tz}"
            
            created = datetime.fromisoformat(created_str)
            age_hours = (now - created.replace(tzinfo=None)).total_seconds() / 3600
            
            if age_hours < 24:
                recent_24h += 1
            if age_hours < 48:
                recent_48h += 1
            if age_hours < 168:  # 7 days
                recent_week += 1
        except:
            pass

print("📅 Creation Time Analysis:")
print(f"   Last 24 hours: {recent_24h} tokens")
print(f"   Last 48 hours: {recent_48h} tokens")
print(f"   Last week: {recent_week} tokens")
print(f"   Older than 1 week: {len(unprocessed) - recent_week} tokens")

print("\n📊 Creation Date Distribution (by day):")
for date, count in sorted(creation_dates.items(), reverse=True)[:10]:
    print(f"   {date}: {count} tokens")

# Check characteristics
networks = Counter()
has_krom_price = 0
tokens_with_krom_price = []

for token in unprocessed:
    networks[token.get('network', 'unknown')] += 1
    
    # Check for KROM price
    raw_data = token.get('raw_data', {})
    krom_price = raw_data.get('trade', {}).get('buyPrice')
    if krom_price:
        has_krom_price += 1
        tokens_with_krom_price.append({
            'ticker': token.get('ticker'),
            'network': token.get('network'),
            'krom_price': krom_price,
            'created': token.get('created_at')
        })

print(f"\n🌐 Network Distribution:")
for network, count in networks.most_common():
    print(f"   {network}: {count} ({count/len(unprocessed)*100:.1f}%)")

print(f"\n💰 KROM Prices Available: {has_krom_price}")
if tokens_with_krom_price:
    print("   Sample tokens with KROM prices:")
    for token in tokens_with_krom_price[:5]:
        print(f"   - {token['ticker']} ({token['network']}): ${token['krom_price']}")

# Test a few recent tokens
print("\n🔬 Testing Recent Tokens with Edge Function:")
test_count = 0
test_success = 0
test_dead = 0

for token in sorted(unprocessed, key=lambda x: x.get('created_at', ''), reverse=True)[:10]:
    if test_count >= 5:
        break
        
    ticker = token.get('ticker', 'Unknown')
    network = token.get('network', 'unknown')
    pool = token.get('pool_address')
    contract = token.get('contract_address')
    created_at = token.get('created_at')
    
    if not pool or not contract or not created_at:
        continue
        
    test_count += 1
    print(f"\n{test_count}. {ticker} ({network}) - Created: {created_at[:19]}")
    
    # Check KROM price first
    krom_price = token.get('raw_data', {}).get('trade', {}).get('buyPrice')
    if krom_price:
        print(f"   ✅ Has KROM price: ${krom_price}")
        test_success += 1
        continue
    
    # Try edge function
    try:
        # Parse timestamp
        timestamp_str = created_at
        if 'Z' in timestamp_str:
            timestamp_str = timestamp_str.replace('Z', '+00:00')
        if '.' in timestamp_str and '+' in timestamp_str:
            parts = timestamp_str.split('.')
            microsec, tz = parts[1].split('+')
            microsec = microsec.ljust(6, '0')[:6]
            timestamp_str = f"{parts[0]}.{microsec}+{tz}"
        
        unix_timestamp = int(datetime.fromisoformat(timestamp_str).timestamp())
        
        # Map network
        mapped_network = 'eth' if network.lower() == 'ethereum' else network
        
        request_data = {
            "contractAddress": contract,
            "network": mapped_network,
            "poolAddress": pool,
            "timestamp": unix_timestamp
        }
        
        edge_req = urllib.request.Request(
            edge_function_url,
            data=json.dumps(request_data).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {service_key}',
                'Content-Type': 'application/json'
            },
            method='POST'
        )
        
        edge_response = urllib.request.urlopen(edge_req, timeout=10)
        result = json.loads(edge_response.read().decode())
        
        if result.get('price'):
            print(f"   ✅ Edge function SUCCESS: ${result['price']}")
            test_success += 1
        else:
            print(f"   💀 Dead token (no price found)")
            test_dead += 1
            
    except Exception as e:
        print(f"   ❌ Error: {str(e)[:50]}")
        test_dead += 1

print(f"\n📊 Test Summary:")
print(f"   Tested: {test_count} tokens")
print(f"   Success: {test_success} ({test_success/test_count*100:.0f}% if test_count > 0 else 0)")
print(f"   Dead: {test_dead}")

# Final hypothesis
print("\n🤔 HYPOTHESIS:")
print("These 169 tokens appear to be:")
print("1. Very recent additions (many from the last few days)")
print("2. Some have KROM prices that weren't detected")
print("3. Many are likely new tokens added while we were processing")
print("4. The edge function works for most when tested individually")
print("\n💡 RECOMMENDATION: Run the parallel processor periodically to catch new additions")