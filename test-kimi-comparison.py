#!/usr/bin/env python3
"""
Compare Kimi K2 native web search vs pre-fetch approach
Tests both speed and cost for website analysis
"""

import os
import json
import requests
import time
from datetime import datetime
from typing import Dict, Any, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPENROUTER_API_KEY = os.getenv('OPEN_ROUTER_API_KEY')
SCRAPERAPI_KEY = os.getenv('SCRAPERAPI_KEY')
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def test_kimi_native_search(website_url: str, ticker: str) -> Tuple[Dict, float, Dict]:
    """
    Option A: Let Kimi K2 fetch and analyze the website itself
    """
    start_time = time.time()
    
    prompt = f"""You are analyzing a cryptocurrency project for legitimacy.

Please visit and analyze this website: {website_url}
Token ticker: {ticker}

Using your web search capabilities, visit the website and analyze:
1. Project legitimacy (score 1-10)
2. Documentation quality
3. Team transparency
4. Technical indicators (whitepaper, audit, roadmap)
5. Red flags and green flags

Provide a JSON response with these fields:
{{
  "website_score": <1-10>,
  "website_tier": <"ALPHA", "SOLID", "BASIC", or "TRASH">,
  "project_category": <"meme", "utility", "defi", etc>,
  "has_documentation": <true/false>,
  "team_visible": <true/false>,
  "red_flags": [list],
  "green_flags": [list],
  "key_findings": "2-3 sentence summary"
}}"""

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
                "temperature": 0.2,
                "max_tokens": 1500,
                "response_format": {"type": "json_object"}
            },
            timeout=60  # Longer timeout for web search
        )
        
        response.raise_for_status()
        result = response.json()
        
        elapsed_time = time.time() - start_time
        
        # Extract token usage for cost calculation
        usage = result.get('usage', {})
        
        if 'choices' in result and len(result['choices']) > 0:
            analysis = json.loads(result['choices'][0]['message']['content'])
            return {
                "success": True,
                "analysis": analysis,
                "method": "native_search"
            }, elapsed_time, usage
        else:
            return {"success": False, "error": "No response"}, elapsed_time, {}
            
    except Exception as e:
        elapsed_time = time.time() - start_time
        return {"success": False, "error": str(e)}, elapsed_time, {}

def test_prefetch_approach(website_url: str, ticker: str) -> Tuple[Dict, float, Dict]:
    """
    Option B: Pre-fetch content with ScraperAPI, then analyze with Kimi
    """
    start_time = time.time()
    total_usage = {}
    
    # Step 1: Fetch with ScraperAPI
    scraper_start = time.time()
    try:
        scraper_url = f"https://api.scraperapi.com/?api_key={SCRAPERAPI_KEY}&url={website_url}"
        response = requests.get(scraper_url, timeout=10)
        response.raise_for_status()
        html_content = response.text[:15000]  # Limit content size
        scraper_time = time.time() - scraper_start
    except Exception as e:
        elapsed_time = time.time() - start_time
        return {"success": False, "error": f"Scraper failed: {e}"}, elapsed_time, {}
    
    # Step 2: Analyze with Kimi K2 (no web search needed)
    kimi_start = time.time()
    
    prompt = f"""You are analyzing a cryptocurrency project website for legitimacy.

Token ticker: {ticker}
Website URL: {website_url}

Website HTML Content (first 15KB):
{html_content}

Analyze the content and provide a JSON response with these fields:
{{
  "website_score": <1-10>,
  "website_tier": <"ALPHA", "SOLID", "BASIC", or "TRASH">,
  "project_category": <"meme", "utility", "defi", etc>,
  "has_documentation": <true/false>,
  "team_visible": <true/false>,
  "red_flags": [list],
  "green_flags": [list],
  "key_findings": "2-3 sentence summary"
}}"""

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
                "temperature": 0.2,
                "max_tokens": 1500,
                "response_format": {"type": "json_object"}
            },
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        kimi_time = time.time() - kimi_start
        
        elapsed_time = time.time() - start_time
        usage = result.get('usage', {})
        
        if 'choices' in result and len(result['choices']) > 0:
            analysis = json.loads(result['choices'][0]['message']['content'])
            return {
                "success": True,
                "analysis": analysis,
                "method": "prefetch",
                "scraper_time": scraper_time,
                "kimi_time": kimi_time
            }, elapsed_time, usage
        else:
            return {"success": False, "error": "No response"}, elapsed_time, {}
            
    except Exception as e:
        elapsed_time = time.time() - start_time
        return {"success": False, "error": str(e)}, elapsed_time, {}

def calculate_costs(usage: Dict, method: str) -> Dict:
    """
    Calculate costs based on token usage
    Kimi K2 pricing via OpenRouter (as of July 2025):
    - Input: $0.14 per 1M tokens
    - Output: $0.28 per 1M tokens
    """
    input_tokens = usage.get('prompt_tokens', 0)
    output_tokens = usage.get('completion_tokens', 0)
    
    # Kimi K2 costs
    input_cost = (input_tokens / 1_000_000) * 0.14
    output_cost = (output_tokens / 1_000_000) * 0.28
    kimi_cost = input_cost + output_cost
    
    # ScraperAPI cost (if prefetch method)
    scraper_cost = 0
    if method == "prefetch":
        # ScraperAPI: 1000 free requests/month, then $49 for 100k requests
        # Estimated: $0.0005 per request after free tier
        scraper_cost = 0.0005  # Conservative estimate
    
    total_cost = kimi_cost + scraper_cost
    
    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "kimi_cost": kimi_cost,
        "scraper_cost": scraper_cost,
        "total_cost": total_cost,
        "cost_per_1000": total_cost * 1000  # Cost per 1000 analyses
    }

def run_comparison_test():
    """
    Run comparison tests on multiple websites
    """
    test_cases = [
        {
            "ticker": "KROM",
            "url": "https://krom.one",
            "description": "Simple landing page"
        },
        {
            "ticker": "UNI",
            "url": "https://uniswap.org",
            "description": "Complex DeFi site"
        },
        {
            "ticker": "PEPE",
            "url": "https://www.pepe.vip",
            "description": "Meme coin site"
        }
    ]
    
    results = []
    
    print("🔬 Kimi K2 Website Analysis Comparison Test")
    print("=" * 60)
    print("Testing: Native Web Search vs Pre-fetch Approach\n")
    
    for test in test_cases:
        print(f"\nTesting: {test['ticker']} - {test['description']}")
        print(f"URL: {test['url']}")
        print("-" * 40)
        
        # Test Native Search
        print("🌐 Testing Native Web Search...")
        native_result, native_time, native_usage = test_kimi_native_search(
            test['url'], test['ticker']
        )
        native_costs = calculate_costs(native_usage, "native")
        
        if native_result.get('success'):
            print(f"  ✅ Success in {native_time:.2f}s")
            print(f"  Score: {native_result['analysis'].get('website_score', 'N/A')}/10")
            print(f"  Tokens: {native_costs['input_tokens']} in / {native_costs['output_tokens']} out")
            print(f"  Cost: ${native_costs['total_cost']:.6f}")
        else:
            print(f"  ❌ Failed: {native_result.get('error')}")
        
        # Small delay between tests
        time.sleep(2)
        
        # Test Pre-fetch Approach
        print("\n📥 Testing Pre-fetch Approach...")
        prefetch_result, prefetch_time, prefetch_usage = test_prefetch_approach(
            test['url'], test['ticker']
        )
        prefetch_costs = calculate_costs(prefetch_usage, "prefetch")
        
        if prefetch_result.get('success'):
            print(f"  ✅ Success in {prefetch_time:.2f}s")
            if 'scraper_time' in prefetch_result:
                print(f"     Scraper: {prefetch_result['scraper_time']:.2f}s")
                print(f"     Kimi: {prefetch_result['kimi_time']:.2f}s")
            print(f"  Score: {prefetch_result['analysis'].get('website_score', 'N/A')}/10")
            print(f"  Tokens: {prefetch_costs['input_tokens']} in / {prefetch_costs['output_tokens']} out")
            print(f"  Cost: ${prefetch_costs['total_cost']:.6f}")
        else:
            print(f"  ❌ Failed: {prefetch_result.get('error')}")
        
        # Compare results
        if native_result.get('success') and prefetch_result.get('success'):
            print("\n📊 Comparison:")
            print(f"  Speed: {'Native' if native_time < prefetch_time else 'Pre-fetch'} is {abs(native_time - prefetch_time):.2f}s faster")
            print(f"  Cost: {'Native' if native_costs['total_cost'] < prefetch_costs['total_cost'] else 'Pre-fetch'} is ${abs(native_costs['total_cost'] - prefetch_costs['total_cost']):.6f} cheaper")
            
            # Check if scores match
            native_score = native_result['analysis'].get('website_score')
            prefetch_score = prefetch_result['analysis'].get('website_score')
            if native_score == prefetch_score:
                print(f"  Accuracy: ✅ Both methods gave same score ({native_score}/10)")
            else:
                print(f"  Accuracy: ⚠️ Different scores - Native: {native_score}/10, Pre-fetch: {prefetch_score}/10")
        
        results.append({
            "ticker": test['ticker'],
            "url": test['url'],
            "native": {
                "success": native_result.get('success'),
                "time": native_time,
                "cost": native_costs['total_cost'],
                "score": native_result['analysis'].get('website_score') if native_result.get('success') else None
            },
            "prefetch": {
                "success": prefetch_result.get('success'),
                "time": prefetch_time,
                "cost": prefetch_costs['total_cost'],
                "score": prefetch_result['analysis'].get('website_score') if prefetch_result.get('success') else None
            }
        })
    
    # Summary
    print("\n" + "=" * 60)
    print("📈 SUMMARY REPORT")
    print("=" * 60)
    
    # Calculate averages
    native_times = [r['native']['time'] for r in results if r['native']['success']]
    prefetch_times = [r['prefetch']['time'] for r in results if r['prefetch']['success']]
    native_costs = [r['native']['cost'] for r in results if r['native']['success']]
    prefetch_costs = [r['prefetch']['cost'] for r in results if r['prefetch']['success']]
    
    if native_times:
        print(f"\n🌐 Native Web Search:")
        print(f"  Average Time: {sum(native_times)/len(native_times):.2f}s")
        print(f"  Average Cost: ${sum(native_costs)/len(native_costs):.6f}")
        print(f"  Cost per 1000: ${sum(native_costs)/len(native_costs) * 1000:.2f}")
    
    if prefetch_times:
        print(f"\n📥 Pre-fetch Approach:")
        print(f"  Average Time: {sum(prefetch_times)/len(prefetch_times):.2f}s")
        print(f"  Average Cost: ${sum(prefetch_costs)/len(prefetch_costs):.6f}")
        print(f"  Cost per 1000: ${sum(prefetch_costs)/len(prefetch_costs) * 1000:.2f}")
    
    # Save detailed results
    output_file = f"kimi_comparison_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {output_file}")

if __name__ == "__main__":
    if not OPENROUTER_API_KEY:
        print("❌ Error: OPEN_ROUTER_API_KEY not found in .env")
        exit(1)
    
    if not SCRAPERAPI_KEY:
        print("⚠️ Warning: SCRAPERAPI_KEY not found, pre-fetch tests may fail")
    
    run_comparison_test()