#!/usr/bin/env python3
"""
Test script for website analysis using Kimi K2 via OpenRouter API
This explores how we can analyze crypto project websites when new calls come in
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Configuration
OPENROUTER_API_KEY = os.getenv('OPEN_ROUTER_API_KEY')
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def fetch_website_content(url: str) -> Optional[str]:
    """
    Fetch website content using WebFetch-like approach
    In production, we'd use a proper scraping service
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # For now, return raw HTML - in production we'd convert to markdown
        return response.text[:10000]  # Limit content size for testing
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def analyze_website_with_kimi(url: str, ticker: str, contract_address: str, content: str = None) -> Dict[str, Any]:
    """
    Analyze a crypto project website using Kimi K2
    """
    # If content not provided, fetch it
    if not content:
        print(f"Fetching website content from {url}...")
        content = fetch_website_content(url)
        if not content:
            return {
                "error": "Failed to fetch website content",
                "url": url
            }
    
    # Create analysis prompt
    prompt = f"""You are a cryptocurrency project analyst. Analyze this website for the token {ticker} (contract: {contract_address}).

Website URL: {url}
Website Content (first 10KB):
{content}

Provide a structured analysis with:

1. **Legitimacy Score** (1-10): Based on website quality, information completeness, professional appearance
2. **Project Type**: Identify if it's a meme coin, utility token, DeFi protocol, etc.
3. **Key Features**: List main features/utilities mentioned
4. **Team Information**: Is team visible? KYC? Anonymous?
5. **Roadmap Status**: Does it have a roadmap? How detailed?
6. **Documentation Quality**: Technical docs, whitepaper, tokenomics explained?
7. **Community Links**: Social media presence (Twitter, Telegram, Discord)
8. **Red Flags**: List any concerning elements (poor grammar, unrealistic promises, copied content)
9. **Green Flags**: List positive indicators (audits, partnerships, clear utility)
10. **Overall Assessment**: Brief summary of whether this looks legitimate

Format as JSON with these exact keys:
- legitimacy_score (1-10)
- project_type (string)
- key_features (array of strings)
- team_visible (boolean)
- has_roadmap (boolean)
- documentation_quality (poor/basic/good/excellent)
- social_links (object with platform names as keys)
- red_flags (array of strings)
- green_flags (array of strings)
- assessment (string, 2-3 sentences)
- confidence (0-1, how confident in this analysis)
"""

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
                "temperature": 0.3,
                "max_tokens": 2000,
                "response_format": {"type": "json_object"}
            }
        )
        
        response.raise_for_status()
        result = response.json()
        
        # Extract the analysis from the response
        if 'choices' in result and len(result['choices']) > 0:
            analysis = json.loads(result['choices'][0]['message']['content'])
            return {
                "success": True,
                "url": url,
                "ticker": ticker,
                "contract_address": contract_address,
                "analysis": analysis,
                "model": "moonshotai/kimi-k2",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "error": "No response from Kimi K2",
                "url": url
            }
            
    except Exception as e:
        return {
            "error": f"Analysis failed: {str(e)}",
            "url": url
        }

def test_website_analysis():
    """
    Test website analysis with a few example crypto projects
    """
    # Test cases - mix of legitimate and questionable projects
    test_cases = [
        {
            "ticker": "KROM",
            "contract": "7JFnQBJoCLkR9DHy3HKayZjvEqUF7Qzi8TCfQRPQpump",
            "url": "https://krom.one",
            "expected": "Legitimate project with clear utility"
        },
        {
            "ticker": "PEPE",
            "contract": "6n7Janary9fqzxKaJVrhL7TG1M62jgNhpF4UPeVeFED",
            "url": "https://www.pepe.vip",
            "expected": "Well-known meme coin"
        },
        {
            "ticker": "UNI",
            "contract": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
            "url": "https://uniswap.org",
            "expected": "Major DeFi protocol"
        }
    ]
    
    results = []
    
    for test in test_cases:
        print(f"\n{'='*60}")
        print(f"Testing: {test['ticker']} - {test['url']}")
        print(f"Expected: {test['expected']}")
        print(f"{'='*60}")
        
        result = analyze_website_with_kimi(
            url=test['url'],
            ticker=test['ticker'],
            contract_address=test['contract']
        )
        
        if result.get('success'):
            analysis = result['analysis']
            print(f"\n✅ Analysis Complete:")
            print(f"  Legitimacy Score: {analysis.get('legitimacy_score', 'N/A')}/10")
            print(f"  Project Type: {analysis.get('project_type', 'Unknown')}")
            print(f"  Assessment: {analysis.get('assessment', 'No assessment')}")
            
            if analysis.get('red_flags'):
                print(f"\n  ⚠️ Red Flags:")
                for flag in analysis['red_flags'][:3]:  # Show first 3
                    print(f"    - {flag}")
            
            if analysis.get('green_flags'):
                print(f"\n  ✅ Green Flags:")
                for flag in analysis['green_flags'][:3]:  # Show first 3
                    print(f"    - {flag}")
        else:
            print(f"\n❌ Analysis Failed: {result.get('error', 'Unknown error')}")
        
        results.append(result)
    
    # Save results for review
    output_file = f"website_analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n\n📊 Results saved to: {output_file}")
    return results

def analyze_single_website(url: str, ticker: str = "TOKEN", contract: str = "0x0"):
    """
    Analyze a single website - useful for testing specific URLs
    """
    print(f"\nAnalyzing {url} for {ticker}...")
    result = analyze_website_with_kimi(url, ticker, contract)
    
    if result.get('success'):
        print(json.dumps(result['analysis'], indent=2))
    else:
        print(f"Error: {result.get('error')}")
    
    return result

if __name__ == "__main__":
    print("🌐 Crypto Website Analysis Test Script")
    print("=" * 60)
    
    if not OPENROUTER_API_KEY:
        print("❌ Error: OPEN_ROUTER_API_KEY not found in .env")
        exit(1)
    
    # Run the test suite
    test_website_analysis()
    
    # Optionally test a specific website
    # analyze_single_website("https://pump.fun", "PUMP", "unknown")