#!/usr/bin/env python3
"""
Monitor ANI token ATH to ensure it stays at the correct value
"""
import requests
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# The correct ATH for ANI (main token)
CORRECT_ATH = 0.08960221
CORRECT_ROI = 23619
ANI_TOKEN_ID = "2c0aea1c-9695-48e8-afa5-b422c10a0314"

print("ANI Token ATH Monitor")
print("=" * 60)
print(f"Expected ATH: ${CORRECT_ATH:.8f} ({CORRECT_ROI}% ROI)")
print("-" * 60)

headers = {
    "apikey": SUPABASE_SERVICE_KEY,
    "Content-Type": "application/json"
}

# Check current value
url = f"{SUPABASE_URL}/rest/v1/crypto_calls?id=eq.{ANI_TOKEN_ID}&select=ticker,ath_price,ath_roi_percent,current_price,ath_last_checked"
response = requests.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()
    if data and len(data) > 0:
        token = data[0]
        current_ath = token.get('ath_price', 0)
        current_roi = token.get('ath_roi_percent', 0)
        current_price = token.get('current_price', 0)
        last_checked = token.get('ath_last_checked', 'Never')
        
        print(f"Current Status:")
        print(f"  ATH Price: ${current_ath:.8f}")
        print(f"  ATH ROI: {current_roi}%")
        print(f"  Current Price: ${current_price:.8f}")
        print(f"  Last Checked: {last_checked}")
        print()
        
        # Check if ATH has been incorrectly modified
        if abs(current_ath - CORRECT_ATH) > 0.000001:
            print("⚠️ WARNING: ATH has been changed!")
            print(f"   Expected: ${CORRECT_ATH:.8f}")
            print(f"   Found: ${current_ath:.8f}")
            print()
            print("Attempting to fix...")
            
            # Fix using Management API
            import json
            fix_query = f"""
                UPDATE crypto_calls 
                SET ath_price = {CORRECT_ATH},
                    ath_roi_percent = {CORRECT_ROI}
                WHERE id = '{ANI_TOKEN_ID}'
            """
            
            api_response = requests.post(
                "https://api.supabase.com/v1/projects/eucfoommxxvqmmwdbkdv/database/query",
                headers={
                    "Authorization": f"Bearer {os.getenv('SUPABASE_ACCESS_TOKEN')}",
                    "Content-Type": "application/json"
                },
                json={"query": fix_query}
            )
            
            if api_response.status_code == 200:
                print("✅ ATH corrected successfully!")
            else:
                print(f"❌ Failed to correct ATH: {api_response.status_code}")
        else:
            print("✅ ATH is correct!")
            
            # Check if current price is higher than ATH (shouldn't be possible)
            if current_price > current_ath:
                print(f"⚠️ Note: Current price (${current_price:.8f}) is higher than ATH!")
                print("   This suggests the ultra-tracker might not be updating properly.")
    else:
        print("❌ Token not found!")
else:
    print(f"❌ Error fetching token: {response.status_code}")

print("\n" + "=" * 60)
print("Monitor complete. Run this script periodically to ensure ATH integrity.")