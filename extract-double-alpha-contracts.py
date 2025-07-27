#!/usr/bin/env python3
"""Extract contract addresses from double ALPHA calls"""

import os
import json
import re
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(url, key)

print("Double ALPHA Calls - Contract Addresses")
print("=" * 60)

# The 3 tickers that got ALPHA from both
double_alpha_data = [
    {
        'ticker': 'THIS YOU?',
        'created': '2025-07-02'
    },
    {
        'ticker': 'BINANCIENS', 
        'created': '2025-06-28'
    },
    {
        'ticker': 'CASE',
        'created': '2025-06-19'
    }
]

for item in double_alpha_data:
    # Get the specific call
    result = supabase.table('crypto_calls') \
        .select('raw_data') \
        .eq('ticker', item['ticker']) \
        .eq('analysis_tier', 'ALPHA') \
        .eq('x_analysis_tier', 'ALPHA') \
        .limit(1) \
        .execute()
    
    if result.data:
        call = result.data[0]
        raw_data = call.get('raw_data')
        
        if raw_data:
            if isinstance(raw_data, str):
                try:
                    raw_data = json.loads(raw_data)
                except:
                    pass
            
            if isinstance(raw_data, dict):
                message = raw_data.get('text', '')
                
                print(f"\n{item['ticker']} ({item['created']})")
                print("-" * 40)
                
                # Extract contract addresses using regex
                # Ethereum addresses (0x...)
                eth_pattern = r'0x[a-fA-F0-9]{40}'
                eth_matches = re.findall(eth_pattern, message)
                
                # Solana addresses (base58, typically 44 chars)
                sol_pattern = r'[1-9A-HJ-NP-Za-km-z]{32,44}'
                
                # Look for pump.fun addresses specifically
                pump_pattern = r'[1-9A-HJ-NP-Za-km-z]{32,44}pump'
                pump_matches = re.findall(pump_pattern, message)
                
                if eth_matches:
                    print(f"Network: Ethereum")
                    print(f"Contract Address: {eth_matches[0]}")
                elif pump_matches:
                    print(f"Network: Solana (pump.fun)")
                    print(f"Contract Address: {pump_matches[0]}")
                else:
                    # Try to find Solana address in common patterns
                    if 'dexscreener.com/solana/' in message:
                        # Extract from dexscreener URL
                        dex_pattern = r'dexscreener\.com/solana/([1-9A-HJ-NP-Za-km-z]{32,44})'
                        dex_match = re.search(dex_pattern, message)
                        if dex_match:
                            print(f"Network: Solana")
                            print(f"Contract Address: {dex_match.group(1)}")
                    else:
                        # Look for standalone Solana addresses
                        words = message.split()
                        for word in words:
                            # Clean up the word
                            clean_word = word.strip('`').strip()
                            if len(clean_word) >= 32 and len(clean_word) <= 44 and clean_word.isalnum():
                                if not clean_word.startswith('0x') and not 'http' in clean_word:
                                    print(f"Network: Solana (likely)")
                                    print(f"Contract Address: {clean_word}")
                                    break