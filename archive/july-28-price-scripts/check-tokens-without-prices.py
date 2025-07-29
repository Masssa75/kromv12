#!/usr/bin/env python3
import json
import urllib.request
import time

print("=== Checking Tokens Without Price Data ===")
print()

supabase_url = "https://eucfoommxxvqmmwdbkdv.supabase.co/rest/v1/crypto_calls"
service_key = None

# Read the service key from .env
try:
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('SUPABASE_SERVICE_ROLE_KEY='):
                service_key = line.split('=', 1)[1].strip()
                break
except:
    print("❌ Could not read .env file")
    exit(1)

# Check different categories
queries = [
    {
        'name': 'Tokens with DEAD_TOKEN source',
        'query': f"{supabase_url}?select=krom_id,ticker,network,price_source&price_source=eq.DEAD_TOKEN&limit=20"
    },
    {
        'name': 'Tokens with null price_source',
        'query': f"{supabase_url}?select=krom_id,ticker,network,price_source&price_source=is.null&limit=20"
    },
    {
        'name': 'Tokens with null historical_price_usd',
        'query': f"{supabase_url}?select=krom_id,ticker,network,historical_price_usd,price_source&historical_price_usd=is.null&limit=20"
    },
    {
        'name': 'Summary of price sources',
        'query': f"{supabase_url}?select=price_source&limit=1000"
    }
]

for query_info in queries:
    print(f"--- {query_info['name']} ---")
    
    req = urllib.request.Request(query_info['query'])
    req.add_header('apikey', service_key)
    req.add_header('Authorization', f'Bearer {service_key}')
    
    try:
        response = urllib.request.urlopen(req)
        results = json.loads(response.read().decode())
        
        if query_info['name'] == 'Summary of price sources':
            # Count price sources
            source_counts = {}
            for result in results:
                source = result.get('price_source', 'null')
                source_counts[source] = source_counts.get(source, 0) + 1
            
            print(f"Price source distribution (from {len(results)} recent records):")
            for source, count in sorted(source_counts.items()):
                print(f"  {source}: {count}")
        else:
            print(f"Found {len(results)} records:")
            for result in results[:10]:  # Show first 10
                ticker = result.get('ticker', 'Unknown')
                network = result.get('network', 'unknown')
                source = result.get('price_source', 'null')
                price = result.get('historical_price_usd', 'null')
                print(f"  {ticker} ({network}) - Source: {source}, Price: {price}")
            
            if len(results) > 10:
                print(f"  ... and {len(results) - 10} more")
        
        print()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print()

print("=== Analysis ===")
print("This will help us understand:")
print("1. How many tokens currently have no price data")
print("2. What the distribution of price sources is")
print("3. Whether we need to run a batch update for historical tokens")