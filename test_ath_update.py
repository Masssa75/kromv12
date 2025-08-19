#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
url = "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-ultra-tracker"
headers = {
    "Authorization": f"Bearer {service_key}",
    "Content-Type": "application/json"
}

print("Testing crypto-ultra-tracker edge function...")
print(f"URL: {url}")

try:
    response = requests.post(url, headers=headers, json={})
    print(f"Response status: {response.status_code}")
    if response.status_code == 200:
        print(f"Success! Response: {response.text[:500]}")
    else:
        print(f"Error response: {response.text}")
except Exception as e:
    print(f"Error: {e}")