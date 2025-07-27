#!/usr/bin/env python3
"""
Test different pagination approaches for KROM API
Try everything until we find what works for downloading ALL historical calls
"""

import os
import requests
import time
import json
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

KROM_API_TOKEN = os.getenv("KROM_API_TOKEN")
BASE_URL = "https://krom.one/api/v1/calls"

def make_request(url, headers):
    """Make API request with error handling"""
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()
        else:
            return f"Status: {response.status_code}"
    except Exception as e:
        return f"Exception: {e}"

def test_pagination_approaches():
    """Test multiple pagination strategies"""
    
    if not KROM_API_TOKEN:
        print("❌ KROM_API_TOKEN not found!")
        return
    
    headers = {'Authorization': f'Bearer {KROM_API_TOKEN}'}
    
    print("🔍 Testing different pagination approaches for KROM API")
    print("=" * 80)
    
    # Get initial batch for reference
    print("1. Getting initial batch...")
    initial_calls = make_request(f"{BASE_URL}?limit=100", headers)
    if isinstance(initial_calls, str):
        print(f"❌ Failed to get initial calls: {initial_calls}")
        return
    
    initial_count = len(initial_calls)
    print(f"✅ Got {initial_count} initial calls")
    
    if initial_count == 0:
        print("No calls to work with!")
        return
    
    # Get reference data
    first_call = initial_calls[0]
    last_call = initial_calls[-1]
    
    print(f"\nFirst call ID: {first_call.get('_id')}")
    print(f"Last call ID: {last_call.get('_id')}")
    print(f"Last call timestamp: {last_call.get('timestamp')}")
    
    # Test different timestamp approaches
    test_methods = []
    
    # Method 1: Use timestamp from last call
    if last_call.get('timestamp'):
        ts = last_call.get('timestamp')
        test_methods.extend([
            f"beforeTimestamp={ts}",
            f"beforeTimestamp={ts * 1000}",  # Milliseconds
            f"before_timestamp={ts}",
            f"timestamp_before={ts}",
            f"until={ts}",
            f"before={ts}",
        ])
    
    # Method 2: Use ID-based pagination
    last_id = last_call.get('_id')
    if last_id:
        test_methods.extend([
            f"before={last_id}",
            f"beforeId={last_id}",
            f"before_id={last_id}",
            f"lastId={last_id}",
            f"cursor={last_id}",
            f"from_id={last_id}",
        ])
    
    # Method 3: Traditional pagination
    test_methods.extend([
        "page=2",
        "page=2&limit=100",
        "offset=100",
        "offset=100&limit=100",
        "skip=100",
        "skip=100&limit=100",
        "start=100",
        "_start=100",
        "_offset=100",
    ])
    
    # Method 4: Try different timestamp formats
    if last_call.get('timestamp'):
        ts = last_call.get('timestamp')
        # Try current time minus some seconds
        current_ts = int(time.time())
        test_methods.extend([
            f"beforeTimestamp={current_ts - 3600}",  # 1 hour ago
            f"beforeTimestamp={current_ts - 86400}",  # 1 day ago
            f"beforeTimestamp={ts - 1}",  # Just before last timestamp
            f"beforeTimestamp={ts - 100}",  # 100 seconds before
        ])
    
    # Method 5: Try different sort orders
    test_methods.extend([
        "sort=timestamp&order=asc",
        "sort=timestamp&order=desc",
        "sort=_id&order=asc",
        "orderBy=timestamp&order=asc",
        "sortBy=timestamp&direction=asc",
    ])
    
    print(f"\n🧪 Testing {len(test_methods)} different methods...")
    print("-" * 80)
    
    working_methods = []
    
    for i, method in enumerate(test_methods, 1):
        url = f"{BASE_URL}?limit=100&{method}"
        print(f"\n{i:2d}. Testing: {method}")
        
        result = make_request(url, headers)
        
        if isinstance(result, str):
            print(f"    ❌ {result}")
            continue
        
        if not result or len(result) == 0:
            print(f"    ❌ Got 0 calls")
            continue
        
        # Check if we got different calls
        new_first_id = result[0].get('_id')
        new_last_id = result[-1].get('_id')
        
        if new_first_id == first_call.get('_id'):
            print(f"    ❌ Got same first call ({new_first_id})")
            continue
        
        print(f"    ✅ SUCCESS! Got {len(result)} different calls")
        print(f"       New first ID: {new_first_id}")
        print(f"       New last ID: {new_last_id}")
        
        # Test if we can paginate again with this method
        if 'beforeTimestamp' in method and result:
            next_ts = result[-1].get('timestamp')
            if next_ts:
                next_url = f"{BASE_URL}?limit=100&beforeTimestamp={next_ts}"
                next_result = make_request(next_url, headers)
                if isinstance(next_result, list) and len(next_result) > 0:
                    if next_result[0].get('_id') != result[0].get('_id'):
                        print(f"    ✅✅ DOUBLE SUCCESS! Can paginate multiple times!")
                        working_methods.append((method, url))
                    else:
                        print(f"    ⚠️  Pagination stopped working on second request")
        else:
            working_methods.append((method, url))
        
        time.sleep(0.5)  # Be nice to the API
    
    print("\n" + "=" * 80)
    print("📊 SUMMARY")
    print("=" * 80)
    
    if working_methods:
        print(f"✅ Found {len(working_methods)} working method(s):")
        for method, url in working_methods:
            print(f"   - {method}")
        
        print("\n🚀 Recommended approach:")
        best_method = working_methods[0][0]
        print(f"   {best_method}")
        
        # Try to download more with the best method
        print(f"\n🧪 Testing extended download with: {best_method}")
        downloaded_calls = []
        current_url = f"{BASE_URL}?limit=100&{best_method}"
        
        for batch in range(5):  # Try 5 batches
            print(f"   Batch {batch + 1}...", end="")
            result = make_request(current_url, headers)
            
            if not isinstance(result, list) or len(result) == 0:
                print(" ❌ Failed")
                break
            
            downloaded_calls.extend(result)
            print(f" ✅ Got {len(result)} calls (total: {len(downloaded_calls)})")
            
            # Prepare next URL based on method type
            if 'beforeTimestamp' in best_method:
                last_ts = result[-1].get('timestamp')
                if last_ts:
                    current_url = f"{BASE_URL}?limit=100&beforeTimestamp={last_ts}"
                else:
                    break
            elif 'before=' in best_method and '_id' in str(result[-1]):
                last_id = result[-1].get('_id')
                current_url = f"{BASE_URL}?limit=100&before={last_id}"
            else:
                break
        
        print(f"\n✅ Extended test downloaded {len(downloaded_calls)} total calls!")
        
    else:
        print("❌ No working pagination methods found!")
        print("\nPossible issues:")
        print("- API might only return latest 100 calls for your key tier")
        print("- Historical data might require different endpoint")
        print("- Rate limiting might be affecting results")
        print("- API behavior might have changed")

if __name__ == "__main__":
    test_pagination_approaches()