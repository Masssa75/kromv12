#!/usr/bin/env python3
"""
Test MR.LEAN token with different timestamps to see when it "died"
"""

import os
import sys
import json
import time
import requests
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

def test_mr_lean_at_timestamp(timestamp, description):
    """Test MR.LEAN token price at a specific timestamp"""
    # MR.LEAN details from our batch
    contract_address = "D5aCKzDfEaKGZhVpbc8DyBJQq3UXW6X8rWYg7BSypump"  # Need to get real contract
    network = "solana"
    
    payload = {
        "contractAddress": contract_address,
        "network": network,
        "callTimestamp": timestamp,
    }
    
    print(f"\n🧪 Testing {description}")
    print(f"   Timestamp: {timestamp} ({datetime.fromtimestamp(timestamp, timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')})")
    
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
            current_price = data.get("currentPrice")
            price_at_call = data.get("priceAtCall") 
            
            if current_price:
                print(f"   ✅ Current Price: ${current_price:.8f}")
            else:
                print(f"   ❌ Current Price: None")
                
            if price_at_call:
                print(f"   📊 Historical Price: ${price_at_call:.8f}")
            else:
                print(f"   📊 Historical Price: None")
                
            return {
                "success": True,
                "current_price": current_price,
                "price_at_call": price_at_call
            }
        else:
            print(f"   ❌ API Error: {response.status_code}")
            print(f"   Details: {response.text[:200]}")
            return {"success": False, "error": response.status_code}
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return {"success": False, "error": str(e)}

def get_mr_lean_real_data():
    """Get the real MR.LEAN data from database"""
    query = f"""
    {SUPABASE_URL}/rest/v1/crypto_calls?
    select=contract_address,network,pool_address,ticker,price_at_call,buy_timestamp,created_at,krom_id&
    krom_id=eq.682a2529eb25eec68c92e87f&
    limit=1
    """.replace('\n', '').replace(' ', '')
    
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json"
    }
    
    response = requests.get(query, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data:
            return data[0]
    
    return None

def main():
    print("🔍 MR.LEAN Token Timeline Analysis")
    print("Testing different timestamps to find when the token 'died'")
    
    # Get real MR.LEAN data
    mr_lean_data = get_mr_lean_real_data()
    if mr_lean_data:
        print(f"\n📋 MR.LEAN Real Data:")
        print(f"   Contract: {mr_lean_data.get('contract_address')}")
        print(f"   Network: {mr_lean_data.get('network')}")
        print(f"   Entry Price: ${mr_lean_data.get('price_at_call')}")
        print(f"   Buy Timestamp: {mr_lean_data.get('buy_timestamp')}")
        print(f"   Created At: {mr_lean_data.get('created_at')}")
        
        # Use real contract address
        global contract_address
        contract_address = mr_lean_data.get('contract_address')
    else:
        print("⚠️  Could not fetch real MR.LEAN data, using example contract")
    
    now = int(time.time())
    
    # Test different time periods
    test_scenarios = [
        (now, "Right now"),
        (now - 60, "1 minute ago"),
        (now - 300, "5 minutes ago"), 
        (now - 1800, "30 minutes ago"),
        (now - 3600, "1 hour ago"),
        (now - 86400, "1 day ago"),
        (now - 604800, "1 week ago"),
        (now - 2592000, "1 month ago"),
    ]
    
    print(f"\n" + "="*60)
    print("TIMELINE ANALYSIS")
    print("="*60)
    
    for timestamp, description in test_scenarios:
        result = test_mr_lean_at_timestamp(timestamp, description)
        time.sleep(0.5)  # Small delay between requests
    
    print(f"\n" + "="*60)
    print("💡 ANALYSIS:")
    print("If historical prices work but current prices don't, the token")
    print("likely had its liquidity removed or was delisted recently.")
    print("="*60)

if __name__ == "__main__":
    main()