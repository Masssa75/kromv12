#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "count=exact"
}

print("Testing count query...")

# Test simple count
query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id&limit=1"
resp = requests.get(query, headers=headers)

print(f"Status: {resp.status_code}")
print(f"Headers: {dict(resp.headers)}")

if 'content-range' in resp.headers:
    total = int(resp.headers['content-range'].split('/')[-1])
    print(f"Total records: {total}")