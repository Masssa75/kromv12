#!/usr/bin/env python3
import subprocess
import json
import urllib.request
from datetime import datetime

# Get service key
service_key = None
with open('.env', 'r') as f:
    for line in f:
        if line.startswith('SUPABASE_SERVICE_ROLE_KEY='):
            service_key = line.split('=', 1)[1].strip()
            break

def get_count():
    url = 'https://eucfoommxxvqmmwdbkdv.supabase.co/rest/v1/crypto_calls?select=*&price_at_call=not.is.null'
    req = urllib.request.Request(url, method='HEAD')
    req.add_header('apikey', service_key)
    req.add_header('Authorization', f'Bearer {service_key}')
    req.add_header('Prefer', 'count=exact')
    
    resp = urllib.request.urlopen(req)
    return int(resp.headers.get('content-range').split('/')[1])

# Get initial count
initial = get_count()
print(f"Starting at: {initial:,} tokens")

# Run the processor for just 30 seconds
try:
    result = subprocess.run(
        ['python3', 'populate-with-progress.py'],
        timeout=30,
        capture_output=True,
        text=True
    )
except subprocess.TimeoutExpired:
    pass

# Get new count
final = get_count()
processed = final - initial

print(f"Processed: {processed} tokens in 30 seconds")
print(f"New total: {final:,} tokens")
print(f"Rate: {processed * 2} tokens/minute")
print(f"Progress: {final/5660*100:.1f}%")