#!/usr/bin/env python3
"""
Website Investment Analyzer - Production-quality scoring based on KROM call analyzer approach
Analyzes crypto project websites for investment legitimacy signals
"""

import os
import json
import sqlite3
import requests
from datetime import datetime
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/Users/marcschwyn/Desktop/projects/KROMV12/.env')

class WebsiteInvestmentAnalyzer:
    """Analyzes crypto websites for investment potential using KROM scoring philosophy"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY') or os.getenv('OPEN_ROUTER_API_KEY')
        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY or OPEN_ROUTER_API_KEY not found in environment")
        
        # Using Kimi K2 - 100x cheaper and better for this type of analysis
        self.model = "moonshotai/kimi-k2"
        
    def create_analysis_prompt(self, website_content: str, ticker: str, contract: str, url: str) -> str:
        """Create the analysis prompt based on KROM call analyzer philosophy"""
        
        return f"""You are analyzing a cryptocurrency project website to assess INVESTMENT LEGITIMACY based on verifiable information. Your goal is to identify tokens backed by credible teams, real products, and transparent operations.

Project Details:
- Token: {ticker}
- Contract: {contract}
- Website: {url}

Website Content:
{website_content[:8000]}

SCORING CRITERIA (based on verifiable legitimacy indicators):
- 8-10: EXCEPTIONAL legitimacy - Verifiable high-profile team/backing, working product with demos, multiple security audits, groundbreaking innovation, substantial documented investment
- 6-7: STRONG legitimacy - Professional operation, transparent team with LinkedIn/GitHub, clear roadmap with achieved milestones, some audits or verification
- 4-5: MODERATE legitimacy - Some credible elements, basic documentation, partial team transparency, demonstrated development effort
- 1-3: LOW/NO legitimacy - Template website, minimal verifiable information, no team details, just basic token existence

SPECIFIC WEBSITE VERIFICATION CHECKS:
1. CONTRACT ADDRESS: Is it displayed on the website? Where exactly? Does it match {contract}?
2. TEAM VERIFICATION: Can team members be verified through LinkedIn/GitHub links?
3. SECURITY: Are audit reports linked or displayed? Which firms?
4. PRODUCT REALITY: Is there a working product, demo, or dashboard accessible?
5. DOCUMENTATION: Quality of whitepaper, technical docs, tokenomics?
6. DEVELOPMENT ACTIVITY: GitHub activity, update frequency, technical depth?
7. PARTNERSHIPS: Any verifiable partnerships with known companies?
8. PROFESSIONALISM: How information is presented (professional writing = professional team)

IMPORTANT PHILOSOPHY:
- When in doubt about something unusual but potentially significant, err on the side of a higher score (5-7 range) and explain your uncertainty
- The way information is communicated reflects legitimacy - professional projects have professional presentation
- Focus on VERIFIABLE information over unsubstantiated claims
- Better to flag potentially important projects for human review than to miss them

Token Type Classification:
- Meme: Community-driven, humor/viral focus, memes, "fun" emphasis
- Utility: Real use case, technical documentation, solving actual problems, DeFi/gaming/infrastructure

Response Format (JSON):
{{
  "investment_score": <1-10>,
  "tier": "<EXCEPTIONAL|STRONG|MODERATE|LOW>",
  "legitimacy_factor": "<High|Medium|Low>",
  "token_type": "<meme|utility>",
  "has_working_product": <true|false>,
  "team_verified": <true|false>,
  "contract_visible": <true|false>,
  "has_audits": <true|false>,
  "project_summary": "<2-3 sentence description of what this project is>",
  "green_flags": ["<positive indicator 1>", "<positive indicator 2>", ...],
  "red_flags": ["<concerning finding 1>", "<concerning finding 2>", ...],
  "reasoning": "<detailed explanation of score including specific findings>",
  "confidence": <0.0-1.0>
}}

Analyze thoroughly and provide JSON response only."""
    
    def fetch_website_content(self, url: str) -> Optional[str]:
        """Fetch website content with basic HTML to text conversion"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                # Basic HTML cleaning
                import re
                text = response.text
                
                # Remove script and style elements
                text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
                text = re.sub(r'<style[^>]*>.*?</style>', '', text, flags=re.DOTALL)
                
                # Extract text from HTML tags
                text = re.sub(r'<[^>]+>', ' ', text)
                
                # Clean up whitespace
                text = ' '.join(text.split())
                
                return text[:10000]  # Limit content size
            
            return None
            
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def analyze_website(self, ticker: str, contract: str, url: str, existing_content: Optional[str] = None) -> Dict[str, Any]:
        """Analyze a website and return investment scoring"""
        
        # Fetch content if not provided
        if existing_content:
            content = existing_content
        else:
            content = self.fetch_website_content(url)
            if not content:
                return {
                    "success": False,
                    "error": "Could not fetch website content",
                    "ticker": ticker
                }
        
        # Create prompt
        prompt = self.create_analysis_prompt(content, ticker, contract, url)
        
        try:
            # Call AI model
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.2,
                    "max_tokens": 1500
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                if 'choices' in result and len(result['choices']) > 0:
                    ai_response = result['choices'][0]['message']['content']
                    
                    # Parse JSON response
                    try:
                        # Extract JSON if wrapped in markdown
                        if '```json' in ai_response:
                            json_str = ai_response.split('```json')[1].split('```')[0]
                        elif '```' in ai_response:
                            json_str = ai_response.split('```')[1].split('```')[0]
                        else:
                            json_str = ai_response
                        
                        analysis = json.loads(json_str)
                        
                        return {
                            "success": True,
                            "ticker": ticker,
                            "contract": contract,
                            "url": url,
                            "analysis": analysis,
                            "analyzed_at": datetime.now().isoformat()
                        }
                        
                    except json.JSONDecodeError as e:
                        return {
                            "success": False,
                            "error": f"Failed to parse AI response: {e}",
                            "raw_response": ai_response,
                            "ticker": ticker
                        }
                else:
                    return {
                        "success": False,
                        "error": "No response from AI model",
                        "ticker": ticker
                    }
            else:
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}",
                    "ticker": ticker
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "ticker": ticker
            }
    
    def analyze_top_tokens(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Analyze top tokens from the database"""
        
        # Connect to database
        conn = sqlite3.connect('analysis_results.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get top tokens by website score
        cursor.execute("""
            SELECT ticker, contract_address, website_url, website_score, 
                   website_tier, website_summary
            FROM website_analysis
            WHERE website_url IS NOT NULL AND website_score IS NOT NULL
            ORDER BY website_score DESC
            LIMIT ?
        """, (limit,))
        
        tokens = cursor.fetchall()
        results = []
        
        print(f"\n🚀 Analyzing {len(tokens)} tokens with investment scoring...")
        print("=" * 60)
        
        for i, token in enumerate(tokens, 1):
            print(f"\n[{i}/{len(tokens)}] Analyzing {token['ticker']}...")
            
            result = self.analyze_website(
                ticker=token['ticker'],
                contract=token['contract_address'],
                url=token['website_url']
            )
            
            if result['success']:
                analysis = result['analysis']
                
                # Store in database
                cursor.execute("""
                    UPDATE website_analysis
                    SET investment_score = ?,
                        investment_tier = ?,
                        investment_summary = ?,
                        investment_green_flags = ?,
                        investment_red_flags = ?,
                        investment_reasoning = ?,
                        investment_analyzed_at = ?
                    WHERE ticker = ?
                """, (
                    analysis['investment_score'],
                    analysis['tier'],
                    analysis['project_summary'],
                    json.dumps(analysis['green_flags']),
                    json.dumps(analysis['red_flags']),
                    analysis['reasoning'],
                    result['analyzed_at'],
                    token['ticker']
                ))
                
                print(f"  ✅ Score: {analysis['investment_score']}/10 ({analysis['tier']})")
                print(f"  📝 {analysis['project_summary'][:100]}...")
                
                results.append(result)
            else:
                print(f"  ❌ Error: {result['error']}")
                results.append(result)
        
        conn.commit()
        conn.close()
        
        return results


def main():
    """Run the investment analyzer on top 20 tokens"""
    
    analyzer = WebsiteInvestmentAnalyzer()
    results = analyzer.analyze_top_tokens(20)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 INVESTMENT ANALYSIS SUMMARY")
    print("=" * 60)
    
    successful = [r for r in results if r.get('success')]
    
    if successful:
        scores = [r['analysis']['investment_score'] for r in successful]
        tiers = {}
        
        for r in successful:
            tier = r['analysis']['tier']
            tiers[tier] = tiers.get(tier, 0) + 1
            
        print(f"\nAnalyzed: {len(successful)}/{len(results)} tokens")
        print(f"Average Score: {sum(scores)/len(scores):.1f}")
        print(f"\nDistribution:")
        for tier in ['EXCEPTIONAL', 'STRONG', 'MODERATE', 'LOW']:
            if tier in tiers:
                print(f"  {tier}: {tiers[tier]} tokens")
    
    print("\n✅ Analysis complete! Results saved to database.")


if __name__ == "__main__":
    main()