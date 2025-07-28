import json
import urllib.request
import os
from datetime import datetime

# Load environment variables
env_vars = {}
with open('.env', 'r') as f:
    for line in f:
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.strip().split('=', 1)
            env_vars[k] = v.strip()

SUPABASE_URL = env_vars['SUPABASE_URL']
SUPABASE_SERVICE_ROLE_KEY = env_vars['SUPABASE_SERVICE_ROLE_KEY']

def get_oldest_50_calls():
    """Get the 50 oldest calls from Supabase"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls"
    url += f"?select=krom_id,ticker,created_at,price_at_call,current_price,ath_price,roi_percent"
    url += f"&order=created_at.asc"  # Ascending order to get oldest first
    url += f"&limit=50"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching calls: {e}")
        return []

def clear_price_data(krom_id):
    """Clear all price-related fields for a specific call"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls?krom_id=eq.{krom_id}"
    
    # Set all price fields to null
    clear_data = {
        "price_at_call": None,
        "current_price": None,
        "ath_price": None,
        "ath_timestamp": None,
        "roi_percent": None,
        "ath_roi_percent": None,
        "market_cap_at_call": None,
        "current_market_cap": None,
        "ath_market_cap": None,
        "fdv_at_call": None,
        "current_fdv": None,
        "ath_fdv": None,
        "price_fetched_at": None,
        "price_network": None,
        "token_supply": None
    }
    
    data = json.dumps(clear_data).encode('utf-8')
    
    req = urllib.request.Request(url, data=data, method='PATCH')
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    req.add_header('Authorization', f'Bearer {SUPABASE_SERVICE_ROLE_KEY}')
    req.add_header('Content-Type', 'application/json')
    req.add_header('Prefer', 'return=representation')  # Return the updated record
    
    try:
        response = urllib.request.urlopen(req)
        if response.status == 200:
            return json.loads(response.read().decode())
        return None
    except Exception as e:
        print(f"Error clearing data for {krom_id}: {e}")
        return None

def verify_other_data_intact(krom_id):
    """Verify that non-price data is still intact"""
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls?krom_id=eq.{krom_id}"
    url += "&select=krom_id,ticker,created_at,raw_data,analysis_score,x_analysis_score"
    
    req = urllib.request.Request(url)
    req.add_header('apikey', SUPABASE_SERVICE_ROLE_KEY)
    
    try:
        response = urllib.request.urlopen(req)
        data = json.loads(response.read().decode())
        if data:
            return data[0]
        return None
    except Exception as e:
        print(f"Error verifying {krom_id}: {e}")
        return None

print("=== Test Clear Price Data for 50 Oldest Calls ===")
print(f"Started at: {datetime.now()}\n")

# Get the oldest 50 calls
print("Fetching 50 oldest calls...")
calls = get_oldest_50_calls()

if not calls:
    print("No calls found!")
else:
    print(f"Found {len(calls)} calls\n")
    
    # Show what we're about to clear
    print("Calls to clear (showing first 10):")
    for i, call in enumerate(calls[:10]):
        created_at = call.get('created_at', 'Unknown')
        ticker = call.get('ticker', 'Unknown')
        has_price = bool(call.get('price_at_call') or call.get('current_price'))
        
        print(f"{i+1}. {ticker} - Created: {created_at[:10]} - Has price data: {has_price}")
    
    if len(calls) > 10:
        print(f"... and {len(calls) - 10} more")
    
    # Count how many have price data
    with_price_data = sum(1 for c in calls if c.get('price_at_call') or c.get('current_price') or c.get('ath_price'))
    print(f"\n{with_price_data} out of {len(calls)} have price data to clear")
    
    # Ask for confirmation
    print("\n" + "="*50)
    print("This will clear all price data for these 50 calls")
    print("But preserve: raw_data, analysis scores, comments, etc.")
    print("="*50)
    
    if input("\nProceed with clearing? (yes/no): ").lower() == 'yes':
        print("\nClearing price data...")
        
        cleared = 0
        failed = 0
        
        for call in calls:
            krom_id = call['krom_id']
            ticker = call.get('ticker', 'Unknown')
            
            # Clear the price data
            result = clear_price_data(krom_id)
            
            if result:
                cleared += 1
                print(f"✅ Cleared {ticker}")
                
                # Verify other data is intact
                verification = verify_other_data_intact(krom_id)
                if verification:
                    has_raw_data = bool(verification.get('raw_data'))
                    has_analysis = verification.get('analysis_score') is not None
                    print(f"   Verified: raw_data={has_raw_data}, analysis_score={has_analysis}")
                else:
                    print(f"   ⚠️  Could not verify other data")
            else:
                failed += 1
                print(f"❌ Failed to clear {ticker}")
        
        print(f"\n=== Summary ===")
        print(f"Successfully cleared: {cleared}")
        print(f"Failed: {failed}")
        
        # Show a sample of cleared data
        if cleared > 0:
            print("\nVerifying first cleared call...")
            first_cleared = get_oldest_50_calls()[0]
            print(f"\nFirst call after clearing ({first_cleared.get('ticker', 'Unknown')}):")
            print(f"  price_at_call: {first_cleared.get('price_at_call', 'None')}")
            print(f"  current_price: {first_cleared.get('current_price', 'None')}")
            print(f"  ath_price: {first_cleared.get('ath_price', 'None')}")
            print(f"  roi_percent: {first_cleared.get('roi_percent', 'None')}")
    else:
        print("\nCancelled - no changes made")

print(f"\nFinished at: {datetime.now()}")