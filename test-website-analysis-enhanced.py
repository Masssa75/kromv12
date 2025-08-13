#!/usr/bin/env python3
"""
Enhanced website analysis for crypto projects - Integration-ready version
This can be easily converted to a Supabase Edge Function
"""

import os
import json
import requests
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from urllib.parse import urlparse

# Load environment variables
load_dotenv()

# API Configuration
OPENROUTER_API_KEY = os.getenv('OPEN_ROUTER_API_KEY')
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def extract_website_from_message(message: str) -> Optional[str]:
    """
    Extract website URL from a crypto call message
    Looks for patterns like website:, site:, or direct URLs
    """
    # Common patterns in crypto calls
    patterns = [
        r'(?:website|site|web):\s*(https?://[^\s]+)',
        r'(?:🌐|💻)\s*(https?://[^\s]+)',
        r'(https?://[^\s]+(?:\.com|\.org|\.io|\.xyz|\.finance|\.one|\.vip|\.fun))',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    
    return None

def get_domain_from_ticker(ticker: str) -> List[str]:
    """
    Generate possible domain names from ticker symbol
    """
    ticker_lower = ticker.lower()
    domains = [
        f"https://{ticker_lower}.com",
        f"https://{ticker_lower}.io",
        f"https://{ticker_lower}.xyz",
        f"https://{ticker_lower}.finance",
        f"https://{ticker_lower}.org",
        f"https://www.{ticker_lower}.com",
        f"https://{ticker_lower}coin.com",
        f"https://{ticker_lower}token.com"
    ]
    return domains

def fetch_website_content_simple(url: str) -> Dict[str, Any]:
    """
    Simple website fetch - in production use ScraperAPI or similar
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=5, allow_redirects=True)
        
        # Get final URL after redirects
        final_url = response.url
        
        # Extract text content (simple version - production would use BeautifulSoup)
        content = response.text[:15000]  # Limit for API context
        
        # Basic content extraction
        title_match = re.search(r'<title>(.*?)</title>', content, re.IGNORECASE)
        title = title_match.group(1) if title_match else "Unknown"
        
        # Look for social links
        twitter_match = re.search(r'(?:twitter\.com|x\.com)/([a-zA-Z0-9_]+)', content)
        telegram_match = re.search(r't\.me/([a-zA-Z0-9_]+)', content)
        
        return {
            "success": True,
            "url": url,
            "final_url": final_url,
            "title": title,
            "content": content,
            "social_links": {
                "twitter": f"@{twitter_match.group(1)}" if twitter_match else None,
                "telegram": f"t.me/{telegram_match.group(1)}" if telegram_match else None
            }
        }
    except requests.exceptions.Timeout:
        return {"success": False, "error": "Website timeout", "url": url}
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": str(e), "url": url}

def analyze_website_for_crypto(
    ticker: str,
    contract_address: str,
    website_url: str = None,
    raw_message: str = None,
    network: str = None
) -> Dict[str, Any]:
    """
    Main function to analyze a crypto project's website
    Can extract URL from message or try common domains
    """
    
    # Try to find website URL
    if not website_url and raw_message:
        website_url = extract_website_from_message(raw_message)
    
    # If still no URL, try common domain patterns
    if not website_url:
        possible_domains = get_domain_from_ticker(ticker)
        for domain in possible_domains[:3]:  # Try first 3
            result = fetch_website_content_simple(domain)
            if result.get("success"):
                website_url = domain
                break
    
    if not website_url:
        return {
            "success": False,
            "error": "No website found",
            "ticker": ticker
        }
    
    # Fetch website content
    website_data = fetch_website_content_simple(website_url)
    if not website_data.get("success"):
        return {
            "success": False,
            "error": f"Failed to fetch website: {website_data.get('error')}",
            "url": website_url
        }
    
    # Prepare analysis prompt
    prompt = f"""You are analyzing a cryptocurrency project website for legitimacy and quality assessment.

Token: {ticker}
Contract: {contract_address}
Network: {network or 'Unknown'}
Website URL: {website_url}
Page Title: {website_data.get('title', 'N/A')}

Website Content (first 15KB):
{website_data['content']}

Analyze and provide a JSON response with these EXACT fields:

{{
  "website_score": <1-10 integer>,
  "website_tier": <"ALPHA", "SOLID", "BASIC", or "TRASH">,
  "project_category": <"meme", "utility", "defi", "gaming", "infrastructure", "unknown">,
  "has_utility": <true/false>,
  "utility_description": <string or null>,
  "team_transparency": <"visible", "partial", "anonymous", "unknown">,
  "documentation_level": <"comprehensive", "basic", "minimal", "none">,
  "social_presence": {{
    "twitter": <handle or null>,
    "telegram": <handle or null>,
    "discord": <true/false>
  }},
  "technical_indicators": {{
    "has_whitepaper": <true/false>,
    "has_roadmap": <true/false>,
    "has_tokenomics": <true/false>,
    "has_audit": <true/false>,
    "contract_verified": <true/false/unknown>
  }},
  "red_flags": [<list of concerning findings>],
  "green_flags": [<list of positive indicators>],
  "key_findings": <2-3 sentence summary>,
  "confidence": <0.0-1.0 float>
}}

Scoring guidelines:
- 9-10: Major protocol, verified team, audited, clear utility
- 7-8: Solid project with good documentation and team
- 5-6: Basic project with some red flags but potential
- 3-4: Minimal effort, likely meme or cash grab
- 1-2: Obvious scam or rug pull indicators

Be strict but fair. Most meme coins score 3-5. Only exceptional projects score 7+."""

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "moonshotai/kimi-k2",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,  # Lower temperature for consistency
                "max_tokens": 1500,
                "response_format": {"type": "json_object"}
            },
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        if 'choices' in result and len(result['choices']) > 0:
            analysis = json.loads(result['choices'][0]['message']['content'])
            
            return {
                "success": True,
                "ticker": ticker,
                "contract_address": contract_address,
                "network": network,
                "website_url": website_url,
                "website_analysis": analysis,
                "social_links_found": website_data.get('social_links', {}),
                "analyzed_at": datetime.now().isoformat(),
                "model": "moonshotai/kimi-k2"
            }
        else:
            return {
                "success": False,
                "error": "No response from AI model",
                "url": website_url
            }
            
    except Exception as e:
        return {
            "success": False,
            "error": f"Analysis failed: {str(e)}",
            "url": website_url
        }

def test_with_real_calls():
    """
    Test with actual crypto calls from the database
    """
    from supabase import create_client
    
    # Initialize Supabase client
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not supabase_url or not supabase_key:
        print("❌ Supabase credentials not found")
        return
    
    supabase = create_client(supabase_url, supabase_key)
    
    # Fetch some recent calls that might have websites
    result = supabase.table('crypto_calls').select(
        'ticker, contract_address, network, raw_data, created_at'
    ).order('created_at', desc=True).limit(5).execute()
    
    if not result.data:
        print("No calls found")
        return
    
    print(f"\n📊 Testing with {len(result.data)} recent crypto calls\n")
    
    for call in result.data:
        print(f"\n{'='*60}")
        print(f"Testing: {call['ticker']} on {call['network']}")
        print(f"Created: {call['created_at']}")
        
        # Extract raw message if available
        raw_message = None
        if call.get('raw_data'):
            raw_data = json.loads(call['raw_data']) if isinstance(call['raw_data'], str) else call['raw_data']
            raw_message = raw_data.get('message', '')
        
        result = analyze_website_for_crypto(
            ticker=call['ticker'],
            contract_address=call['contract_address'],
            network=call['network'],
            raw_message=raw_message
        )
        
        if result.get('success'):
            analysis = result['website_analysis']
            print(f"\n✅ Website Analysis Complete:")
            print(f"  URL Found: {result['website_url']}")
            print(f"  Score: {analysis['website_score']}/10 ({analysis['website_tier']})")
            print(f"  Category: {analysis['project_category']}")
            print(f"  Has Utility: {analysis['has_utility']}")
            print(f"  Key Findings: {analysis['key_findings']}")
            
            # Update database with website analysis
            update_data = {
                'website_url': result['website_url'],
                'website_score': analysis['website_score'],
                'website_tier': analysis['website_tier'],
                'website_analysis': json.dumps(analysis),
                'website_analyzed_at': result['analyzed_at']
            }
            
            # Would update here in production
            # supabase.table('crypto_calls').update(update_data).eq('contract_address', call['contract_address']).execute()
            
        else:
            print(f"\n❌ Analysis Failed: {result.get('error')}")

def main():
    """
    Main test function
    """
    print("🌐 Enhanced Website Analysis for Crypto Projects")
    print("=" * 60)
    
    # Test with a known good project
    print("\n1️⃣ Testing with known project (Uniswap)...")
    result = analyze_website_for_crypto(
        ticker="UNI",
        contract_address="0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
        website_url="https://uniswap.org",
        network="ethereum"
    )
    
    if result.get('success'):
        print(json.dumps(result['website_analysis'], indent=2))
    
    # Test URL extraction from message
    print("\n2️⃣ Testing URL extraction from call message...")
    test_message = "🚀 New gem alert! $MOON is launching! Website: https://mooncoin.xyz Join TG: t.me/mooncoin"
    
    url = extract_website_from_message(test_message)
    print(f"  Extracted URL: {url}")
    
    # Test with real database calls
    print("\n3️⃣ Testing with real crypto calls from database...")
    test_with_real_calls()

if __name__ == "__main__":
    main()