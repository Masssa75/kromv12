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

# Get all unprocessed tokens
url = f"{supabase_url}?select=*&price_at_call=is.null&price_source=is.null&order=created_at.desc"
req = urllib.request.Request(url)
req.add_header('apikey', service_key)
req.add_header('Authorization', f'Bearer {service_key}')

response = urllib.request.urlopen(req)
unprocessed = json.loads(response.read().decode())

print(f"=== Analysis of {len(unprocessed)} Unprocessed Tokens ===\n")

# 1. Check basic characteristics
networks = Counter()
has_pool = 0
has_contract = 0
has_buy_timestamp = 0
has_krom_price = 0
has_created_at = 0
no_timestamps = []
recent_tokens = []

for token in unprocessed:
    # Network distribution
    networks[token.get('network', 'unknown')] += 1
    
    # Check fields
    if token.get('pool_address'):
        has_pool += 1
    if token.get('contract_address'):
        has_contract += 1
    if token.get('buy_timestamp'):
        has_buy_timestamp += 1
    if token.get('created_at'):
        has_created_at += 1
        # Check if recently added
        try:
            # Handle various timestamp formats
            created_str = token['created_at']
            if 'Z' in created_str:
                created_str = created_str.replace('Z', '+00:00')
            # Handle non-standard microseconds
            if '.' in created_str:
                parts = created_str.split('.')
                if '+' in parts[1]:
                    microsec, tz = parts[1].split('+')
                    # Pad microseconds to 6 digits
                    microsec = microsec.ljust(6, '0')[:6]
                    created_str = f"{parts[0]}.{microsec}+{tz}"
            created = datetime.fromisoformat(created_str)
            if (datetime.now(created.tzinfo) - created).days < 2:
                recent_tokens.append(token)
        except Exception as e:
            pass
    
    # Check for KROM price
    raw_data = token.get('raw_data', {})
    if raw_data.get('trade', {}).get('buyPrice'):
        has_krom_price += 1
    
    # Track tokens with no timestamps
    if not token.get('buy_timestamp') and not token.get('created_at'):
        no_timestamps.append(token)

print("📊 Basic Statistics:")
print(f"   Has pool address: {has_pool}/{len(unprocessed)} ({has_pool/len(unprocessed)*100:.1f}%)")
print(f"   Has contract address: {has_contract}/{len(unprocessed)} ({has_contract/len(unprocessed)*100:.1f}%)")
print(f"   Has buy_timestamp: {has_buy_timestamp}/{len(unprocessed)} ({has_buy_timestamp/len(unprocessed)*100:.1f}%)")
print(f"   Has created_at: {has_created_at}/{len(unprocessed)} ({has_created_at/len(unprocessed)*100:.1f}%)")
print(f"   Has KROM price: {has_krom_price}/{len(unprocessed)} ({has_krom_price/len(unprocessed)*100:.1f}%)")

print(f"\n🌐 Network Distribution:")
for network, count in networks.most_common():
    print(f"   {network}: {count} ({count/len(unprocessed)*100:.1f}%)")

print(f"\n⏰ Timing Analysis:")
print(f"   Recently added (last 2 days): {len(recent_tokens)} tokens")
print(f"   No timestamps at all: {len(no_timestamps)} tokens")

# 2. Sample some problematic tokens
print(f"\n🔍 Sample of Unprocessed Tokens:")
for i, token in enumerate(unprocessed[:5]):
    print(f"\n{i+1}. {token.get('ticker', 'Unknown')} ({token.get('network', 'unknown')})")
    print(f"   KROM ID: {token.get('krom_id')}")
    print(f"   Pool: {'Yes' if token.get('pool_address') else 'NO'}")
    print(f"   Contract: {'Yes' if token.get('contract_address') else 'NO'}")
    print(f"   Buy timestamp: {'Yes' if token.get('buy_timestamp') else 'NO'}")
    print(f"   Created at: {token.get('created_at', 'NO')}")
    print(f"   KROM price: {token.get('raw_data', {}).get('trade', {}).get('buyPrice', 'NO')}")

# 3. Find tokens that SHOULD be processable
processable = []
for token in unprocessed:
    if (token.get('pool_address') and 
        token.get('contract_address') and 
        (token.get('buy_timestamp') or token.get('created_at'))):
        processable.append(token)

print(f"\n⚠️ Tokens that SHOULD be processable: {len(processable)}")
if processable:
    print("Sample of processable tokens:")
    for token in processable[:5]:
        print(f"   - {token['ticker']} ({token['network']}) - Created: {token.get('created_at', 'N/A')[:10]}")

# 4. Check for patterns in creation dates
if unprocessed:
    dates = []
    for token in unprocessed:
        if token.get('created_at'):
            dates.append(token['created_at'][:10])
    
    date_counts = Counter(dates)
    print(f"\n📅 Creation Date Distribution (top 10):")
    for date, count in date_counts.most_common(10):
        print(f"   {date}: {count} tokens")

# 5. Check for missing essential data
missing_essentials = []
for token in unprocessed:
    issues = []
    if not token.get('pool_address'):
        issues.append('no pool')
    if not token.get('contract_address'):
        issues.append('no contract')
    if not token.get('buy_timestamp') and not token.get('created_at'):
        issues.append('no timestamp')
    
    if issues:
        missing_essentials.append({
            'ticker': token.get('ticker', 'Unknown'),
            'network': token.get('network', 'unknown'),
            'issues': ', '.join(issues)
        })

print(f"\n❌ Tokens with Missing Essential Data: {len(missing_essentials)}")
if missing_essentials:
    for token in missing_essentials[:10]:
        print(f"   - {token['ticker']} ({token['network']}): {token['issues']}")

# Save detailed report
with open('unprocessed_tokens_report.json', 'w') as f:
    report = {
        'summary': {
            'total_unprocessed': len(unprocessed),
            'has_pool': has_pool,
            'has_contract': has_contract,
            'has_timestamps': has_buy_timestamp + has_created_at,
            'should_be_processable': len(processable),
            'recent_additions': len(recent_tokens)
        },
        'network_distribution': dict(networks),
        'processable_samples': processable[:20],
        'missing_essentials': missing_essentials[:50]
    }
    json.dump(report, f, indent=2)

print(f"\n📄 Detailed report saved to: unprocessed_tokens_report.json")