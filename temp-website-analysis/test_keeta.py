#!/usr/bin/env python3
"""
Test Keeta website to see if CA is in their docs
"""

import os
import sys
import requests
from dotenv import load_dotenv

sys.path.append('..')
load_dotenv('../.env')

OPEN_ROUTER_API_KEY = os.getenv('OPEN_ROUTER_API_KEY')

def check_keeta_docs():
    prompt = """Visit https://keeta.com and thoroughly explore the website, including any documentation, whitepaper, or technical docs.

IMPORTANT: Look for a Solana contract address (base58 format, typically 44 characters) in:
1. Main website pages
2. Documentation section (if there's a docs link)
3. Whitepaper or litepaper
4. FAQ or Help sections
5. Footer or header areas
6. Any "Token" or "Tokenomics" pages
7. Developer documentation
8. Buy/Trade button destinations

Also note:
- What is Keeta? What do they do?
- Do they have extensive documentation?
- Is there a clear connection to a token?
- Any links to DEXes or trading platforms?

Return your findings in detail. If you find any contract addresses, list them exactly as shown."""

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
    
    print("Checking Keeta website and documentation...")
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
    check_keeta_docs()