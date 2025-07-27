#!/usr/bin/env python3
"""Get KROMV12 project API keys"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

access_token = os.getenv("SUPABASE_ACCESS_TOKEN")
base_url = "https://api.supabase.com"

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json"
}

# KROMV12 project ID
project_id = "eucfoommxxvqmmwdbkdv"

print(f"Fetching API keys for KROMV12 project...")
print(f"Project ID: {project_id}")
print("=" * 60)

# Get project API keys
keys_response = requests.get(f"{base_url}/v1/projects/{project_id}/api-keys", headers=headers)

if keys_response.status_code == 200:
    keys = keys_response.json()
    
    print("\nProject URLs and Keys:")
    print(f"SUPABASE_URL=https://{project_id}.supabase.co")
    
    for key in keys:
        if key['name'] == 'anon':
            print(f"SUPABASE_ANON_KEY={key['api_key']}")
        elif key['name'] == 'service_role':
            print(f"SUPABASE_SERVICE_ROLE_KEY={key['api_key']}")
else:
    print(f"Error: {keys_response.status_code}")
    print(keys_response.text)