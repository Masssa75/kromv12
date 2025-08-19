#!/usr/bin/env python3
"""
Test batch website checking with first 60 tokens
"""

import os
import requests
import json
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

# Initialize Supabase client
supabase_url = os.getenv('SUPABASE_URL')
supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase: Client = create_client(supabase_url, supabase_key)

print("Testing batch website discovery...")
print("=" * 60)

# Get first 60 tokens
print("Fetching first 60 tokens...")
response = supabase.table('token_discovery').select('id, contract_address, symbol, network').limit(60).execute()
tokens = response.data
print(f"Got {len(tokens)} tokens")

# Split into 2 batches of 30
batch1 = tokens[:30]
batch2 = tokens[30:60] if len(tokens) > 30 else []

stats = {
    'with_website': 0,
    'with_twitter': 0,
    'with_telegram': 0,
    'total': len(tokens)
}

for batch_num, batch in enumerate([batch1, batch2], 1):
    if not batch:
        continue
        
    print(f"\nBatch {batch_num}: {len(batch)} tokens")
    
    # Create comma-separated list of addresses
    addresses = ','.join([t['contract_address'] for t in batch])
    
    # Fetch from DexScreener
    url = f"https://api.dexscreener.com/latest/dex/tokens/{addresses}"
    
    try:
        response = requests.get(url, headers={'Accept': 'application/json'})
        data = response.json()
        
        # Process results
        for pair in data.get('pairs', []):
            info = pair.get('info', {})
            if info:
                if info.get('websites'):
                    stats['with_website'] += 1
                    symbol = pair.get('baseToken', {}).get('symbol', '?')
                    print(f"  ✅ {symbol}: Has website")
                    
                socials = info.get('socials', [])
                for social in socials:
                    if social.get('type') == 'twitter':
                        stats['with_twitter'] += 1
                    elif social.get('type') == 'telegram':
                        stats['with_telegram'] += 1
                        
    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "=" * 60)
print("RESULTS:")
print(f"Total tokens checked: {stats['total']}")
print(f"Tokens with websites: {stats['with_website']} ({stats['with_website']*100/stats['total']:.1f}%)")
print(f"Tokens with Twitter: {stats['with_twitter']} ({stats['with_twitter']*100/stats['total']:.1f}%)")
print(f"Tokens with Telegram: {stats['with_telegram']} ({stats['with_telegram']*100/stats['total']:.1f}%)")