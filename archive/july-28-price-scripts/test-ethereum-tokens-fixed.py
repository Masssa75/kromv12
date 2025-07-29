#!/usr/bin/env python3
"""
Test the failed Ethereum tokens with network mapping fix
"""

import os
import sys
import json
import time
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# Headers for Supabase API calls
headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json"
}

def fetch_current_price_with_mapping(contract_address, network, pool_address=None):
    """Fetch current price using the crypto-price-single edge function with network mapping"""
    # Network mapping - KROM stores "ethereum" but GeckoTerminal API requires "eth"
    network_map = {
        'ethereum': 'eth',
        'solana': 'solana',
        'bsc': 'bsc',
        'polygon': 'polygon',
        'arbitrum': 'arbitrum',
        'base': 'base'
    }
    
    mapped_network = network_map.get(network, network)
    print(f"         Network mapping: {network} → {mapped_network}")
    
    payload = {
        "contractAddress": contract_address,
        "network": mapped_network,
        "callTimestamp": int(time.time()),
    }
    
    if pool_address:
        payload["poolAddress"] = pool_address
    
    try:
        response = requests.post(
            f"{SUPABASE_URL}/functions/v1/crypto-price-single",
            headers={
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=20
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                "success": True,
                "current_price": data.get("currentPrice"),
                "duration": data.get("duration")
            }
        else:
            return {
                "success": False,
                "error": f"Status {response.status_code}",
                "details": response.text[:200]
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}

def main():
    print("🧪 Testing Failed Ethereum Tokens with Network Mapping Fix")
    print()
    
    # The Ethereum tokens that failed from our previous batch
    failed_ethereum_tokens = [
        {
            "ticker": "VITALIKSAMA",
            "krom_id": "682a1a32eb25eec68c92e434",
            "contract": "0xFf803a6E81bb93574385bAB7183d1e2f0e59e2eA",
            "network": "ethereum",
            "entry_price": 1.242e-07
        },
        {
            "ticker": "TOR", 
            "krom_id": "682a1d85eb25eec68c92e560",
            "contract": "0x1fDb319cC1bE16ff75EF84e408b0BC2cF5cA9b00",  # Example - would need real contract
            "network": "ethereum",
            "entry_price": 0.0417092056
        },
        {
            "ticker": "PEPEV2",
            "krom_id": "682a2064eb25eec68c92e688", 
            "contract": "0x2b591e99afe9f32eaa6214f7b7629768c40eeb39",  # Example PEPE contract
            "network": "ethereum",
            "entry_price": 2.431e-07
        }
    ]
    
    successful = 0
    failed = 0
    
    for i, token in enumerate(failed_ethereum_tokens, 1):
        print(f"[{i}/3] {token['ticker']} ({token['krom_id']})")
        print(f"        Contract: {token['contract']}")
        print(f"        Entry: ${token['entry_price']}")
        
        # Test with network mapping
        result = fetch_current_price_with_mapping(
            token['contract'], 
            token['network']
        )
        
        if result["success"] and result["current_price"]:
            current_price = result["current_price"]
            duration = result.get("duration", "N/A")
            
            if token['entry_price'] > 0:
                roi = ((current_price - token['entry_price']) / token['entry_price']) * 100
                print(f"        ✅ Current: ${current_price:.8f} | ROI: {roi:+.1f}% ({duration}s)")
            else:
                print(f"        ✅ Current: ${current_price:.8f} ({duration}s)")
            successful += 1
        else:
            error = result.get("error", "Unknown error")
            details = result.get("details", "")[:100]
            print(f"        ❌ {error}")
            if details:
                print(f"        Details: {details}")
            failed += 1
        
        print()
        time.sleep(0.5)
    
    print(f"🎉 Test Complete! ✅ {successful} successful, ❌ {failed} failed")
    if successful > 0:
        print("🔧 Network mapping fix is working! Ready to update the batch script.")
    else:
        print("⚠️  These tokens may still be genuinely dead/delisted.")

if __name__ == "__main__":
    main()