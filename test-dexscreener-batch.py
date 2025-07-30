import requests
import json

# Test DexScreener batch API with multiple tokens
print("=== TESTING DEXSCREENER BATCH API ===")

# Test with some known tokens
test_addresses = [
    "9rB2Dmbdn4KpepcVgNCCmgS7yKgYA2RQx5auoWkhbonk",  # OZZY (Solana)
    "0x4b3e8d491Eb7cb96DE014bD0E3C2d675209065cF",  # MCAP (Ethereum)
    "DFfPq2hHbJJ4jD5ArD7KYAc9bfgJBJ4Y4YoXdUCPump"   # KITTY (Solana)
]

addresses = ",".join(test_addresses)
print(f"\nRequesting: {addresses[:50]}...\n")

response = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{addresses}")

if response.status_code == 200:
    data = response.json()
    print(f"Response has {len(data.get('pairs', []))} pairs\n")
    
    # Group pairs by token
    tokens_found = {}
    for pair in data.get('pairs', []):
        token_address = pair['baseToken']['address'].lower()
        if token_address not in tokens_found:
            tokens_found[token_address] = []
        tokens_found[token_address].append(pair)
    
    print(f"Found {len(tokens_found)} unique tokens\n")
    
    # Show details for each token
    for token_addr, pairs in tokens_found.items():
        print(f"Token: {token_addr[:10]}...")
        print(f"  Symbol: {pairs[0]['baseToken']['symbol']}")
        print(f"  Found {len(pairs)} pair(s)")
        
        # Show all pair prices
        for i, pair in enumerate(pairs[:3]):  # Show first 3 pairs
            print(f"  Pair {i+1}:")
            print(f"    DEX: {pair['dexId']}")
            print(f"    Price: ${pair['priceUsd']}")
            print(f"    Liquidity: ${pair.get('liquidity', {}).get('usd', 'N/A')}")
            print(f"    Chain: {pair['chainId']}")
        print()
    
    # Check which requested tokens were NOT found
    print("\n=== CHECKING WHICH TOKENS WERE FOUND ===")
    for addr in test_addresses:
        if addr.lower() in tokens_found:
            print(f"✅ {addr[:10]}... FOUND")
        else:
            print(f"❌ {addr[:10]}... NOT FOUND")
            
else:
    print(f"API Error: {response.status_code}")
    print(response.text)
