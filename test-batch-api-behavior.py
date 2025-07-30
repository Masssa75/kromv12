import requests
import json

print("=== TESTING DEXSCREENER BATCH API BEHAVIOR ===")

# Test with FINESHYT and a few other tokens
test_addresses = [
    "SLajyzj8kDbKB7358aYJc2aoWBW4Jquea4Dm3LMpump",  # FINESHYT
    "EzaNX1MHGzwAMHJahgLVWLzXBvHBtmP2uvufAdofpump",  # BIP177
    "9rB2Dmbdn4KpepcVgNCCmgS7yKgYA2RQx5auoWkhbonk"   # OZZY
]

print("\nTesting batch request with 3 tokens...")
addresses = ",".join(test_addresses)

response = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{addresses}")

if response.status_code == 200:
    data = response.json()
    print(f"\nResponse contains {len(data.get('pairs', []))} pairs total\n")
    
    # Group by token
    by_token = {}
    for pair in data.get('pairs', []):
        token_addr = pair['baseToken']['address']
        if token_addr not in by_token:
            by_token[token_addr] = []
        by_token[token_addr].append(pair)
    
    # Analyze each token
    for token_addr, pairs in by_token.items():
        print(f"Token: {pairs[0]['baseToken']['symbol']} ({token_addr[:20]}...)")
        print(f"  Found {len(pairs)} pair(s)")
        
        if len(pairs) > 1:
            print("  \n  MULTIPLE PAIRS FOUND:")
            for i, pair in enumerate(pairs[:5]):  # Show first 5
                print(f"  Pair {i+1}:")
                print(f"    Price: ${pair['priceUsd']}")
                print(f"    Liquidity: ${pair.get('liquidity', {}).get('usd', 'N/A')}")
                print(f"    Volume 24h: ${pair.get('volume', {}).get('h24', 'N/A')}")
                print(f"    DEX: {pair['dexId']}")
                print(f"    Pair Address: {pair['pairAddress'][:20]}...")
                print()
        else:
            print(f"  Single pair: ${pairs[0]['priceUsd']}")
        print()
    
    # Check if FINESHYT is in the response
    fineshyt_found = False
    for pair in data.get('pairs', []):
        if pair['baseToken']['address'] == test_addresses[0]:
            fineshyt_found = True
            print(f"\nFINESHYT found in response:")
            print(f"  Price: ${pair['priceUsd']}")
            print(f"  Symbol: {pair['baseToken']['symbol']}")
            break
    
    if not fineshyt_found:
        print("\n❌ FINESHYT NOT FOUND in batch response!")
        print("This might be why it has wrong price - it's using data from another token!")
        
else:
    print(f"API Error: {response.status_code}")
