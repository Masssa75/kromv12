import os
from supabase import create_client, Client
from dotenv import load_dotenv
import requests
import json

load_dotenv()

url = os.environ.get('SUPABASE_URL')
key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

print("=== DEBUGGING PRICE MISMATCH ISSUE ===")
print("Testing how batch API might return wrong prices...\n")

# Get a few tokens to test
tokens = supabase.table('crypto_calls').select('krom_id, ticker, contract_address, network, current_price').not_.is_('contract_address', 'null').not_.is_('current_price', 'null').limit(5).execute()

print("Testing with these tokens:")
for t in tokens.data:
    print(f"  {t['ticker']}: {t['contract_address']}")

# Make batch request
addresses = ",".join([t['contract_address'] for t in tokens.data])
print(f"\nBatch request with {len(tokens.data)} addresses...\n")

response = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{addresses}")

if response.status_code == 200:
    data = response.json()
    print(f"API returned {len(data.get('pairs', []))} pairs\n")
    
    # Show what the API returned
    print("=== API RESPONSE ===")
    for pair in data.get('pairs', []):
        print(f"Token: {pair['baseToken']['symbol']} ({pair['baseToken']['address']})")
        print(f"  Price: ${pair['priceUsd']}")
        print(f"  Chain: {pair['chainId']}")
        print()
    
    # Now simulate what the refresh-prices code does
    print("\n=== SIMULATING REFRESH-PRICES MATCHING ===")
    
    for pair in data.get('pairs', []):
        contractAddress = pair['baseToken']['address'].lower()
        
        # Find matching token
        originalToken = None
        for t in tokens.data:
            if t['contract_address'].lower() == contractAddress:
                originalToken = t
                break
        
        if originalToken:
            print(f"\n✅ MATCHED: {originalToken['ticker']}")
            print(f"  Contract matches: {contractAddress}")
            print(f"  Would update price to: ${pair['priceUsd']}")
            print(f"  Current DB price: ${originalToken['current_price']}")
        else:
            print(f"\n❌ NO MATCH for {pair['baseToken']['symbol']}")
            print(f"  API contract: {contractAddress}")
            print(f"  DB contracts: {[t['contract_address'].lower() for t in tokens.data]}")
            
            # Check if there's a partial match
            for t in tokens.data:
                if contractAddress[:10] in t['contract_address'].lower():
                    print(f"  ⚠️  PARTIAL MATCH with {t['ticker']}: {t['contract_address']}")

print("\n=== HYPOTHESIS ===")
print("If multiple tokens share similar contract prefixes, or if the API")
print("returns tokens in a different order than requested, prices could")
print("be assigned to the wrong tokens!")
