#!/usr/bin/env python3
"""
Test if Kimi K2 can web search to verify contract addresses
"""

import os
import sys
import requests
from dotenv import load_dotenv

sys.path.append('..')
load_dotenv('../.env')

OPEN_ROUTER_API_KEY = os.getenv('OPEN_ROUTER_API_KEY')

def test_web_search():
    # Note: That looks like an Ethereum address, not Solana. Let's test both scenarios
    
    prompt = """Please perform a web search for the following contract address and determine if it's associated with Keeta (keeta.com):

Contract Address: 0xc0634090f2fe6c6d75e61be2b949464abb498973

Search for:
1. This exact contract address on search engines
2. "Keeta token contract" or "Keeta CA" 
3. Check if this contract appears on:
   - Etherscan or other block explorers
   - CoinGecko or CoinMarketCap pages for Keeta
   - DexScreener listings
   - Twitter/X posts from official Keeta accounts
   - Telegram or Discord announcements

Tell me:
- What search engine(s) you're using
- What you find about this contract
- Is this the official Keeta token contract?
- Where did you find the verification (which sources)?

Also search for "Keeta token Solana" to see if there's a Solana version."""

    headers = {
        'Authorization': f'Bearer {OPEN_ROUTER_API_KEY}',
        'Content-Type': 'application/json',
    }
    
    data = {
        'model': 'moonshotai/kimi-k2',
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.3,
        'max_tokens': 2000
    }
    
    print("Testing Kimi K2 web search capabilities...")
    print("=" * 60)
    
    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=90
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            print(content)
        else:
            print(f"Error: {response.status_code}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_web_search()