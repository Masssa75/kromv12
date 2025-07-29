#!/usr/bin/env python3
"""Debug the cron analyze endpoint to see what errors are occurring"""

import requests
import json

# Test the direct analyze endpoint first (known working)
print("1. Testing direct /api/analyze endpoint...")
try:
    response = requests.post(
        'https://lively-torrone-8199e0.netlify.app/api/analyze',
        headers={'Content-Type': 'application/json'},
        json={'limit': 1, 'model': 'moonshotai/kimi-k2'},
        timeout=30
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Success: Processed {result.get('count', 0)} calls")
        if result.get('results'):
            print(f"   Sample result: {result['results'][0]['token']} - Score: {result['results'][0]['score']}")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
except Exception as e:
    print(f"❌ Exception: {e}")

# Test cron analyze endpoint
print("\n2. Testing cron /api/cron/analyze endpoint...")
try:
    response = requests.get(
        'https://lively-torrone-8199e0.netlify.app/api/cron/analyze?auth=a07066e62da04a115fde8f18813a931b16095bbaa2fac17dfd6cd0d9662ae30b',
        timeout=60  # Longer timeout for cron job
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"Status: Success={result.get('success')}")
        print(f"Processed: {result.get('processed')}/{result.get('total')}")
        print(f"Errors: {result.get('errors')}")
        print(f"Model: {result.get('model')}")
        print(f"Duration: {result.get('duration')}")
        
        if result.get('errors', 0) > 0:
            print("❌ Errors occurred but no details provided in response")
            print("   Need to check Netlify function logs for actual error messages")
    else:
        print(f"❌ Failed: {response.status_code} - {response.text}")
except Exception as e:
    print(f"❌ Exception: {e}")

print("\n3. Comparison:")
print("   - Direct API: Works perfectly")
print("   - Cron API: Reports errors but no error details")
print("   - Both use same OpenRouter API key")
print("   - Issue likely in cron endpoint's specific implementation")

print("\n4. Next steps:")
print("   - Check Netlify function logs for detailed error messages")
print("   - Look for differences in data processing between endpoints")
print("   - Consider timeout or memory issues in cron endpoint")
print("   - May need to modify cron endpoint to return error details")