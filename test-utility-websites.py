#!/usr/bin/env python3
"""
Test website analysis for utility tokens
Fetches website URLs from DexScreener API (same as KROM modal)
Then analyzes with Kimi K2's native web search
"""

import os
import json
import requests
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

# API Configuration
OPENROUTER_API_KEY = os.getenv('OPEN_ROUTER_API_KEY')
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

def fetch_token_info_from_dexscreener(contract_address: str, network: str) -> Dict[str, Any]:
    """
    Fetch token info from DexScreener API (same as KROM modal does)
    This mimics the /api/token-info endpoint behavior
    """
    try:
        # DexScreener expects addresses in lowercase
        address = contract_address.lower()
        
        # For Solana, use the contract directly
        # For EVM chains, might need chain prefix
        url = f"https://api.dexscreener.com/latest/dex/tokens/{address}"
        
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('pairs') or len(data['pairs']) == 0:
            return {"success": False, "error": "No pairs found"}
        
        # Get the first pair (usually highest liquidity)
        pair = data['pairs'][0]
        
        # Extract social links (website, twitter, telegram)
        socials = pair.get('info', {}).get('socials', [])
        
        website_url = None
        twitter_url = None
        telegram_url = None
        
        for social in socials:
            if social['type'] == 'website':
                website_url = social.get('url')
            elif social['type'] == 'twitter':
                twitter_url = social.get('url')
            elif social['type'] == 'telegram':
                telegram_url = social.get('url')
        
        # Also check for direct website in info
        if not website_url and pair.get('info', {}).get('websites'):
            websites = pair['info']['websites']
            if isinstance(websites, list) and len(websites) > 0:
                website_url = websites[0].get('url') if isinstance(websites[0], dict) else websites[0]
        
        return {
            "success": True,
            "website": website_url,
            "twitter": twitter_url,
            "telegram": telegram_url,
            "price_usd": pair.get('priceUsd'),
            "liquidity_usd": pair.get('liquidity', {}).get('usd'),
            "volume_24h": pair.get('volume', {}).get('h24'),
            "pair_address": pair.get('pairAddress'),
            "dex": pair.get('dexId'),
            "chain": pair.get('chainId')
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}

def analyze_website_with_kimi(ticker: str, contract_address: str, website_url: str, network: str) -> Dict[str, Any]:
    """
    Use Kimi K2's native web search to analyze a crypto website
    """
    prompt = f"""You are analyzing a cryptocurrency project for legitimacy and quality.

Token: {ticker}
Contract: {contract_address}
Network: {network}
Website: {website_url}

Please visit and analyze the website {website_url} using your web search capabilities.

Evaluate:
1. Project legitimacy (1-10 score)
2. Documentation quality (whitepaper, docs, tokenomics)
3. Team transparency (visible team, KYC, anonymous)
4. Technical indicators (audit, roadmap, github)
5. Utility description (what does this token actually do?)
6. Red flags (suspicious elements, copied content, unrealistic promises)
7. Green flags (audits, partnerships, working product)

Provide a JSON response with these EXACT fields:
{{
  "website_score": <1-10 integer>,
  "website_tier": <"ALPHA", "SOLID", "BASIC", or "TRASH">,
  "project_category": <"utility", "defi", "gaming", "infrastructure", "social", "meme", "unknown">,
  "has_real_utility": <true/false>,
  "utility_description": <string describing the actual utility or null>,
  "documentation_quality": <"comprehensive", "good", "basic", "minimal", "none">,
  "team_transparency": <"fully_visible", "partial", "anonymous", "unknown">,
  "has_audit": <true/false>,
  "has_whitepaper": <true/false>,
  "has_roadmap": <true/false>,
  "has_working_product": <true/false>,
  "red_flags": [<array of concerning findings>],
  "green_flags": [<array of positive indicators>],
  "key_findings": <2-3 sentence summary>,
  "confidence": <0.0-1.0 float>
}}

Be strict in evaluation. Most projects score 3-5. Only exceptional projects with real utility, strong teams, and working products score 7+."""

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
                "max_tokens": 2000,
                "response_format": {"type": "json_object"}
            },
            timeout=60  # Longer timeout for web search
        )
        
        response.raise_for_status()
        result = response.json()
        
        if 'choices' in result and len(result['choices']) > 0:
            analysis = json.loads(result['choices'][0]['message']['content'])
            return {
                "success": True,
                "analysis": analysis,
                "model": "moonshotai/kimi-k2",
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {"success": False, "error": "No response from Kimi K2"}
            
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"Invalid JSON response: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Analysis failed: {str(e)}"}

def test_utility_tokens():
    """
    Test website analysis for utility tokens from the database
    """
    # Initialize Supabase
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Fetch utility tokens (non-dead, oldest first)
    print("📊 Fetching utility tokens from database...")
    result = supabase.table('crypto_calls').select(
        'id, ticker, contract_address, network, analysis_token_type, created_at, is_dead, ath_roi_percent'
    ).eq('analysis_token_type', 'utility').eq('is_dead', False).order('created_at').limit(5).execute()
    
    if not result.data:
        print("No active utility tokens found")
        return
    
    print(f"Found {len(result.data)} active utility tokens\n")
    
    results = []
    tokens_with_websites = 0
    
    for i, token in enumerate(result.data, 1):
        print(f"\n{'='*60}")
        print(f"Token {i}/{len(result.data)}: {token['ticker']} on {token['network']}")
        print(f"Contract: {token['contract_address'][:20]}...")
        print(f"Created: {token['created_at'][:10]}")
        print(f"ATH ROI: {token.get('ath_roi_percent', 0):.0f}%")
        
        # Step 1: Fetch token info from DexScreener
        print("\n📡 Fetching from DexScreener...")
        token_info = fetch_token_info_from_dexscreener(
            token['contract_address'],
            token['network']
        )
        
        if not token_info.get('success'):
            print(f"  ❌ Failed: {token_info.get('error')}")
            results.append({
                "token": token,
                "website_found": False,
                "error": token_info.get('error')
            })
            continue
        
        website_url = token_info.get('website')
        
        if not website_url:
            print(f"  ⚠️ No website URL found on DexScreener")
            print(f"  Twitter: {token_info.get('twitter') or 'None'}")
            print(f"  Telegram: {token_info.get('telegram') or 'None'}")
            results.append({
                "token": token,
                "website_found": False,
                "dexscreener_data": token_info
            })
            continue
        
        tokens_with_websites += 1
        print(f"  ✅ Website found: {website_url}")
        print(f"  Liquidity: ${token_info.get('liquidity_usd', 0):,.0f}")
        print(f"  Volume 24h: ${token_info.get('volume_24h', 0):,.0f}")
        
        # Step 2: Analyze website with Kimi K2
        print(f"\n🔍 Analyzing website with Kimi K2...")
        analysis_result = analyze_website_with_kimi(
            token['ticker'],
            token['contract_address'],
            website_url,
            token['network']
        )
        
        if analysis_result.get('success'):
            analysis = analysis_result['analysis']
            print(f"  ✅ Analysis complete:")
            print(f"  Score: {analysis['website_score']}/10 ({analysis['website_tier']})")
            print(f"  Category: {analysis['project_category']}")
            print(f"  Has Real Utility: {analysis['has_real_utility']}")
            if analysis.get('utility_description'):
                print(f"  Utility: {analysis['utility_description'][:100]}...")
            print(f"  Documentation: {analysis['documentation_quality']}")
            print(f"  Team: {analysis['team_transparency']}")
            
            if analysis.get('green_flags'):
                print(f"\n  ✅ Green Flags:")
                for flag in analysis['green_flags'][:3]:
                    print(f"    - {flag}")
            
            if analysis.get('red_flags'):
                print(f"\n  ⚠️ Red Flags:")
                for flag in analysis['red_flags'][:3]:
                    print(f"    - {flag}")
            
            print(f"\n  📝 Summary: {analysis['key_findings']}")
            
            # Prepare database update
            update_data = {
                'website_url': website_url,
                'website_score': analysis['website_score'],
                'website_tier': analysis['website_tier'],
                'website_analysis': json.dumps(analysis),
                'website_analyzed_at': datetime.now().isoformat()
            }
            
            # Update database (commented out for testing)
            # supabase.table('crypto_calls').update(update_data).eq('id', token['id']).execute()
            # print(f"\n  💾 Database updated with website analysis")
            
        else:
            print(f"  ❌ Analysis failed: {analysis_result.get('error')}")
        
        results.append({
            "token": token,
            "website_found": True,
            "website_url": website_url,
            "dexscreener_data": token_info,
            "analysis": analysis_result
        })
        
        # Rate limiting
        time.sleep(2)
    
    # Summary
    print(f"\n{'='*60}")
    print("📈 SUMMARY")
    print(f"{'='*60}")
    print(f"Total tokens tested: {len(result.data)}")
    print(f"Tokens with websites: {tokens_with_websites} ({tokens_with_websites/len(result.data)*100:.0f}%)")
    
    successful_analyses = [r for r in results if r.get('analysis', {}).get('success')]
    if successful_analyses:
        scores = [r['analysis']['analysis']['website_score'] for r in successful_analyses]
        print(f"Successfully analyzed: {len(successful_analyses)}")
        print(f"Average website score: {sum(scores)/len(scores):.1f}/10")
        
        # Group by tier
        tiers = {}
        for r in successful_analyses:
            tier = r['analysis']['analysis']['website_tier']
            tiers[tier] = tiers.get(tier, 0) + 1
        print(f"Tier distribution: {tiers}")
    
    # Save results
    output_file = f"utility_website_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n💾 Detailed results saved to: {output_file}")

if __name__ == "__main__":
    print("🌐 Utility Token Website Analysis Test")
    print("=" * 60)
    
    if not OPENROUTER_API_KEY:
        print("❌ Error: OPEN_ROUTER_API_KEY not found in .env")
        exit(1)
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Error: Supabase credentials not found in .env")
        exit(1)
    
    test_utility_tokens()