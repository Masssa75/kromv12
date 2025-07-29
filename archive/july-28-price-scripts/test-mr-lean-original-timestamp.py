#!/usr/bin/env python3
"""
Test MR.LEAN with its original call timestamp to see if we can reproduce the entry price
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

def get_mr_lean_full_data():
    """Get complete MR.LEAN data from database"""
    query = f"""
    {SUPABASE_URL}/rest/v1/crypto_calls?
    select=*&
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

def test_with_original_data(mr_lean_data):
    """Test with the original call data"""
    contract_address = mr_lean_data.get('contract_address')
    network = mr_lean_data.get('network')
    pool_address = mr_lean_data.get('pool_address')
    created_at = mr_lean_data.get('created_at')
    buy_timestamp = mr_lean_data.get('buy_timestamp')
    
    # Convert created_at to timestamp if buy_timestamp is missing
    if buy_timestamp:
        call_timestamp = int(datetime.fromisoformat(buy_timestamp.replace('Z', '+00:00')).timestamp())
    elif created_at:
        call_timestamp = int(datetime.fromisoformat(created_at.replace('Z', '+00:00')).timestamp())
    else:
        call_timestamp = int(time.time())
    
    print(f"🧪 Testing MR.LEAN with Original Call Data")
    print(f"   Contract: {contract_address}")
    print(f"   Network: {network}")
    print(f"   Pool Address: {pool_address}")
    print(f"   Call Timestamp: {call_timestamp}")
    print(f"   Call Date: {datetime.fromtimestamp(call_timestamp, timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}")
    print(f"   Known Entry Price: ${mr_lean_data.get('price_at_call')}")
    
    payload = {
        "contractAddress": contract_address,
        "network": network,
        "callTimestamp": call_timestamp,
    }
    
    # Add pool address if available
    if pool_address:
        payload["poolAddress"] = pool_address
        print(f"   ✅ Using pool address: {pool_address}")
    else:
        print(f"   ⚠️  No pool address available")
    
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
        
        print(f"\n📡 API Response:")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ Success!")
            print(f"   Current Price: ${data.get('currentPrice') or 'None'}")
            print(f"   Historical Price: ${data.get('priceAtCall') or 'None'}")
            print(f"   Duration: {data.get('duration', 'N/A')}s")
            
            # Check if we got the expected entry price
            expected_price = mr_lean_data.get('price_at_call')
            actual_price = data.get('priceAtCall')
            
            if expected_price and actual_price:
                diff_percent = abs(expected_price - actual_price) / expected_price * 100
                print(f"\n💰 Price Comparison:")
                print(f"   Expected: ${expected_price:.8f}")
                print(f"   Actual: ${actual_price:.8f}")
                print(f"   Difference: {diff_percent:.2f}%")
                
                if diff_percent < 5:
                    print(f"   ✅ Prices match (within 5%)")
                else:
                    print(f"   ⚠️  Prices differ significantly")
            
            return data
        else:
            print(f"   ❌ Failed")
            print(f"   Error: {response.text[:300]}")
            return None
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return None

def main():
    print("🔍 MR.LEAN Original Timestamp Test")
    print("Testing with the exact same parameters used for the entry price")
    
    # Get complete MR.LEAN data
    mr_lean_data = get_mr_lean_full_data()
    
    if not mr_lean_data:
        print("❌ Could not fetch MR.LEAN data")
        return
    
    print(f"\n📋 Complete MR.LEAN Data:")
    for key, value in mr_lean_data.items():
        if key not in ['raw_data']:  # Skip raw_data as it's too long
            print(f"   {key}: {value}")
    
    print(f"\n" + "="*60)
    
    # Test with original parameters
    result = test_with_original_data(mr_lean_data)
    
    print(f"\n" + "="*60)
    print("💡 CONCLUSIONS:")
    if result:
        print("✅ Edge function is working with original parameters")
        if result.get('priceAtCall'):
            print("✅ Historical price fetch succeeded")
        if result.get('currentPrice'):
            print("✅ Current price fetch succeeded")
        else:
            print("❌ Current price fetch failed - token likely dead now")
    else:
        print("❌ Edge function failed completely")
        print("🤔 This suggests the token data might be corrupted or the")
        print("   original entry price came from a different source")

if __name__ == "__main__":
    main()