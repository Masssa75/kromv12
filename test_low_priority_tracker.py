#!/usr/bin/env python3
import os
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
url = "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-ultra-tracker-low"
headers = {
    "Authorization": f"Bearer {service_key}",
    "Content-Type": "application/json"
}

print("Testing crypto-ultra-tracker-low ($1K-$20K liquidity)...")
print(f"URL: {url}")
print("\nExpected: ~2,082 tokens with liquidity $1K-$20K")
print("-" * 50)

start_time = time.time()

try:
    response = requests.post(
        url, 
        headers=headers, 
        json={"maxTokens": 2200},  # Should handle all ~2,082 tokens
        timeout=120
    )
    
    elapsed = time.time() - start_time
    
    print(f"\nResponse status: {response.status_code}")
    print(f"Time taken: {elapsed:.1f} seconds")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ SUCCESS! Low-priority tracker is working!")
        print("-" * 50)
        print(f"Total tokens processed: {data.get('totalTokens', 0)}")
        print(f"Tokens updated: {data.get('totalUpdated', 0)}")
        print(f"New ATHs found: {data.get('newATHs', 0)}")
        print(f"API calls made: {data.get('apiCalls', 0)}")
        print(f"Processing time: {data.get('processingTimeMs', 0)/1000:.1f}s")
        print(f"Tokens per second: {data.get('tokensPerSecond', 0)}")
        
        if data.get('totalTokens', 0) > 2000:
            print(f"\n⚠️ Warning: Processing {data.get('totalTokens', 0)} tokens may be close to limit")
            print("Consider splitting further if issues arise")
    else:
        print(f"\n❌ Error: {response.text[:200]}")
        
except requests.Timeout:
    print(f"\n⚠️ Request timed out after {elapsed:.1f} seconds")
except Exception as e:
    print(f"\n❌ Error: {e}")