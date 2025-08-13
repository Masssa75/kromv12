#!/usr/bin/env python3
"""
Test Kimi K2's web search capabilities for token verification
"""

import os
import sys
import json
import requests
from dotenv import load_dotenv

sys.path.append('..')
load_dotenv('../.env')

OPEN_ROUTER_API_KEY = os.getenv('OPEN_ROUTER_API_KEY')

def test_web_search_verification(ticker="KEETA", network="Base", contract_address=None):
    """
    Test Kimi K2's ability to do autonomous web searches for token verification
    """
    
    # Create a prompt that encourages multi-step web search
    prompt = f"""I need you to verify the legitimacy and find the official contract address for the {ticker} token on {network}.

IMPORTANT: Use web search to find information from multiple sources. Don't just visit one website.

SEARCH STRATEGY:
1. First, search Google for "{ticker} token {network} contract address"
2. Look for official sources like:
   - The project's official Twitter/X account
   - Block explorer (BaseScan, Etherscan, etc.) 
   - CoinGecko or CoinMarketCap listings
   - DEX listings (Uniswap, PancakeSwap, etc.)
   - Official project announcements

3. Cross-reference the contract address across multiple sources
4. Check for verification badges on explorers
5. Look for trading volume and liquidity to confirm it's active

WHAT TO FIND:
- Official contract address
- Market cap and trading volume
- Official website (if any)
- Official Twitter/X handle
- Which DEXs it trades on
- Any security audits or verifications
- Whether ownership is renounced
- Whether liquidity is locked

BE THOROUGH: Visit at least 3-5 different sources to verify the information.

Return a detailed JSON with your findings:
{{
    "ticker": "{ticker}",
    "network": "{network}",
    "contract_address": "<verified contract address>",
    "verification_sources": [
        {{
            "source_type": "twitter|explorer|dex|coingecko|website|etc",
            "source_url": "<URL>",
            "contract_found": "<contract if mentioned>",
            "additional_info": "<what you learned>"
        }}
    ],
    "market_data": {{
        "market_cap": "<amount>",
        "daily_volume": "<amount>",
        "liquidity": "<amount>",
        "main_dex": "<where it trades>"
    }},
    "social_links": {{
        "website": "<URL if found>",
        "twitter": "<handle if found>",
        "telegram": "<link if found>"
    }},
    "security_info": {{
        "ownership_renounced": <true|false|unknown>,
        "liquidity_locked": <true|false|unknown>,
        "audit_status": "<info if available>"
    }},
    "legitimacy_score": <0-10>,
    "legitimacy_reasoning": "<explain your confidence level>",
    "search_path": ["<step 1>", "<step 2>", "<step 3>", "..."]
}}

IMPORTANT: Show me your complete search journey in the "search_path" array."""

    headers = {
        'Authorization': f'Bearer {OPEN_ROUTER_API_KEY}',
        'Content-Type': 'application/json',
    }
    
    data = {
        'model': 'moonshotai/kimi-k2',
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.3,
        'max_tokens': 4000  # Allow for detailed response
    }
    
    print(f"Testing Kimi K2's web search capabilities for {ticker} on {network}...")
    print("=" * 80)
    print("Sending request to Kimi K2...")
    print("-" * 80)
    
    try:
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=60  # Longer timeout for web searches
        )
        
        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content']
            
            print("Raw Response:")
            print(content[:500] + "..." if len(content) > 500 else content)
            print("\n" + "=" * 80)
            
            # Try to extract JSON
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = content[json_start:json_end]
                try:
                    verification_data = json.loads(json_str)
                    
                    print("\n📊 VERIFICATION RESULTS")
                    print("=" * 80)
                    
                    # Contract Address
                    print(f"✅ Contract: {verification_data.get('contract_address', 'Not found')}")
                    
                    # Verification Sources
                    print(f"\n📍 Verified from {len(verification_data.get('verification_sources', []))} sources:")
                    for source in verification_data.get('verification_sources', []):
                        print(f"  • {source['source_type']}: {source.get('source_url', 'N/A')[:50]}...")
                        if source.get('contract_found'):
                            print(f"    Contract: {source['contract_found'][:20]}...")
                    
                    # Market Data
                    market = verification_data.get('market_data', {})
                    if market:
                        print(f"\n💰 Market Data:")
                        print(f"  • Market Cap: {market.get('market_cap', 'Unknown')}")
                        print(f"  • Daily Volume: {market.get('daily_volume', 'Unknown')}")
                        print(f"  • Main DEX: {market.get('main_dex', 'Unknown')}")
                    
                    # Social Links
                    social = verification_data.get('social_links', {})
                    if social:
                        print(f"\n🔗 Social Links:")
                        for platform, link in social.items():
                            if link:
                                print(f"  • {platform}: {link}")
                    
                    # Security Info
                    security = verification_data.get('security_info', {})
                    if security:
                        print(f"\n🔒 Security:")
                        print(f"  • Ownership: {'Renounced ✅' if security.get('ownership_renounced') else 'Not Renounced ⚠️'}")
                        print(f"  • Liquidity: {'Locked ✅' if security.get('liquidity_locked') else 'Not Locked ⚠️'}")
                    
                    # Legitimacy Score
                    print(f"\n🎯 Legitimacy Score: {verification_data.get('legitimacy_score', 0)}/10")
                    print(f"📝 Reasoning: {verification_data.get('legitimacy_reasoning', 'No reasoning provided')}")
                    
                    # Search Path (shows what Kimi did)
                    search_path = verification_data.get('search_path', [])
                    if search_path:
                        print(f"\n🔍 Search Journey ({len(search_path)} steps):")
                        for i, step in enumerate(search_path, 1):
                            print(f"  {i}. {step}")
                    
                    return verification_data
                    
                except json.JSONDecodeError as e:
                    print(f"Failed to parse JSON: {e}")
                    print(f"JSON string: {json_str[:200]}...")
            
        else:
            print(f"API Error: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"Error: {e}")
        
    return None

def test_multiple_tokens():
    """Test several tokens to understand Kimi's capabilities"""
    test_cases = [
        {"ticker": "KEETA", "network": "Base"},
        {"ticker": "PEPE", "network": "Ethereum"},
        {"ticker": "BRIX", "network": "Base"},
    ]
    
    for test in test_cases:
        print("\n" + "🚀" * 40)
        print(f"TESTING: {test['ticker']} on {test['network']}")
        print("🚀" * 40)
        
        result = test_web_search_verification(
            ticker=test['ticker'],
            network=test['network']
        )
        
        if result:
            # Save results
            filename = f"kimi_search_test_{test['ticker'].lower()}.json"
            with open(filename, 'w') as f:
                json.dump(result, f, indent=2)
            print(f"\n💾 Results saved to {filename}")
        
        print("\n" + "=" * 80)
        input("Press Enter to continue to next token...")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Kimi K2 web search capabilities')
    parser.add_argument('--ticker', type=str, default='KEETA', help='Token ticker to search')
    parser.add_argument('--network', type=str, default='Base', help='Network the token is on')
    parser.add_argument('--all', action='store_true', help='Test multiple tokens')
    
    args = parser.parse_args()
    
    if args.all:
        test_multiple_tokens()
    else:
        test_web_search_verification(args.ticker, args.network)