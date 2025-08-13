#!/usr/bin/env python3
"""
Verify Keeta contract on Base network
"""

import os
import sys
import requests
from dotenv import load_dotenv

sys.path.append('..')
load_dotenv('../.env')

OPEN_ROUTER_API_KEY = os.getenv('OPEN_ROUTER_API_KEY')

def verify_keeta_base():
    prompt = """Please search for information about this contract address on Base network (not Ethereum mainnet):

Contract: 0xc0634090f2fe6c6d75e61be2b949464abb498973
Network: Base (Base chain, Coinbase's L2)

Search for:
1. This contract on BaseScan (Base block explorer)
2. "Keeta Base token" or "Keeta Base contract"
3. Check DexScreener for Base pairs with this contract
4. Look for official Keeta announcements about Base deployment
5. Search Twitter/X for "@keetaxyz" or official Keeta accounts mentioning this contract
6. Check if this is listed on:
   - CoinGecko as Keeta on Base
   - DexScreener Base pairs
   - Any Base DEXes (Aerodrome, BaseSwap, etc.)

Important: Distinguish between:
- Ethereum mainnet (chain ID 1)
- Base network (chain ID 8453)

Tell me:
- Is this the legitimate Keeta token on Base?
- Where did you find verification?
- Any official links or announcements?
- Trading volume and legitimacy indicators"""

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
    
    print("Verifying Keeta contract on Base network...")
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
    verify_keeta_base()