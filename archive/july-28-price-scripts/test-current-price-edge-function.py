#!/usr/bin/env python3
"""
Test the crypto-price-single edge function for current price fetching
"""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# Test with a known contract
test_contracts = [
    {
        "name": "WETH (Ethereum)",
        "contract": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "network": "eth"
    },
    {
        "name": "USDC (Ethereum)", 
        "contract": "0xA0b86a33E6441d58B8A6E1A5E27A0b9Ec4F2D7c1",
        "network": "eth"
    }
]

def test_edge_function(contract_address, network, name):
    payload = {
        "contractAddress": contract_address,
        "network": network,
        "callTimestamp": 1706140800  # Some timestamp
    }
    
    print(f"\n🧪 Testing {name}")
    print(f"   Contract: {contract_address}")
    print(f"   Network: {network}")
    
    try:
        response = requests.post(
            f"{SUPABASE_URL}/functions/v1/crypto-price-single",
            headers={
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success!")
            print(f"   💰 Current Price: ${data.get('currentPrice', 'N/A')}")
            print(f"   📊 Market Cap: ${data.get('currentMarketCap', 'N/A')}")
            print(f"   ⏱️  Duration: {data.get('duration', 'N/A')}s")
            return True
        else:
            print(f"   ❌ Failed: {response.status_code}")
            print(f"   📄 Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    print("🧪 Testing crypto-price-single Edge Function")
    print(f"🔗 URL: {SUPABASE_URL}/functions/v1/crypto-price-single")
    
    success_count = 0
    
    for test in test_contracts:
        if test_edge_function(test["contract"], test["network"], test["name"]):
            success_count += 1
    
    print(f"\n📊 Results: {success_count}/{len(test_contracts)} tests passed")

if __name__ == "__main__":
    main()