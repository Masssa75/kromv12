#!/usr/bin/env python3
"""
Enhanced crypto call analyzer with 1-10 scoring system
Designed to identify high-value tokens like NOT (Binance) and KEETA (Google backing)
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Tuple
from supabase import create_client
from anthropic import Anthropic
import google.generativeai as genai
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

class EnhancedCryptoAnalyzer:
    def __init__(self):
        # Initialize Supabase
        self.supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        )
        
        # Initialize AI clients
        self.anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
        self.gemini = genai.GenerativeModel('gemini-pro')
        self.openai = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
    def get_analysis_prompt(self, call_data: Dict) -> str:
        """Create detailed prompt for natural language analysis"""
        return f"""Analyze this crypto call for legitimacy and potential value. 

CRITICAL: This is for research purposes to identify truly valuable projects like:
- NOT/NOTCOIN: Backed by Binance, tweeted by CZ
- KEETA/KITA: $17M funding, ex-Google CEO as investor

Call Details:
- Ticker: {call_data.get('ticker', 'Unknown')}
- Message: {call_data.get('raw_data', {}).get('text', 'No message')}
- Group: {call_data.get('raw_data', {}).get('group', {}).get('name', 'Unknown')}

Score on a 1-10 scale:
1-3: Complete shitcoin (just contract address, no info)
4-7: Some legitimacy (unknown team, small company)
8-10: Major backing (Binance, Google, major VCs, famous founders)

Provide:
1. Score (1-10)
2. Legitimacy factor (1-6 words max)
3. Brief explanation

IMPORTANT: 
- Use ONLY natural language processing, no keyword matching
- Look for genuine signals of major backing or innovation
- Be extremely selective with 8+ scores
- No mock data or assumptions

Format response as JSON:
{{
  "score": <number>,
  "legitimacy_factor": "<short phrase>",
  "explanation": "<brief explanation>"
}}"""

    def get_tweet_analysis_prompt(self, ticker: str, tweets: List[Dict]) -> str:
        """Create prompt for tweet analysis"""
        tweet_texts = "\n\n".join([f"Tweet {i+1}: {t.get('text', '')}" for i, t in enumerate(tweets)])
        
        return f"""Analyze these tweets about {ticker} crypto token for legitimacy signals.

CRITICAL: Looking for tokens with backing like:
- NOT/NOTCOIN: Binance backing, CZ tweet
- KEETA: Google/ex-Google CEO investment, $17M funding

Tweets:
{tweet_texts}

Score 1-10:
1-3: Just spam/hype
4-7: Some project info
8-10: Major institutional backing/partnerships

Provide:
1. Score (1-10)
2. Best tweet (most legitimate info)
3. Legitimacy factor (1-6 words)
4. Brief explanation

Format as JSON:
{{
  "score": <number>,
  "best_tweet": "<full text of best tweet>",
  "legitimacy_factor": "<short phrase>",
  "explanation": "<brief explanation>"
}}"""

    async def analyze_with_claude(self, prompt: str, model: str = "claude-3-haiku-20240307") -> Tuple[Dict, str]:
        """Analyze with Claude API"""
        try:
            response = self.anthropic.messages.create(
                model=model,
                max_tokens=500,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = json.loads(response.content[0].text)
            return result, model
        except Exception as e:
            print(f"Claude analysis error: {e}")
            return None, model

    async def analyze_with_gemini(self, prompt: str) -> Tuple[Dict, str]:
        """Analyze with Gemini API"""
        try:
            response = self.gemini.generate_content(prompt)
            result = json.loads(response.text)
            return result, "gemini-pro"
        except Exception as e:
            print(f"Gemini analysis error: {e}")
            return None, "gemini-pro"

    async def analyze_with_gpt(self, prompt: str, model: str = "gpt-4") -> Tuple[Dict, str]:
        """Analyze with OpenAI GPT"""
        try:
            response = self.openai.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            result = json.loads(response.choices[0].message.content)
            return result, model
        except Exception as e:
            print(f"GPT analysis error: {e}")
            return None, model

    async def analyze_batch(self, limit: int = 10, model_preference: str = "claude"):
        """Analyze a batch of calls"""
        print(f"Fetching {limit} calls for enhanced analysis...")
        
        # Get calls that need enhanced analysis
        calls = self.supabase.table('crypto_calls') \
            .select('*') \
            .is_('analysis_score', 'null') \
            .not_.is_('raw_data', 'null') \
            .limit(limit) \
            .execute()
        
        if not calls.data:
            print("No calls need enhanced analysis")
            return
        
        print(f"Analyzing {len(calls.data)} calls with {model_preference}...")
        
        for call in calls.data:
            print(f"\nAnalyzing {call['ticker']} (ID: {call['krom_id']})")
            
            # Get analysis prompt
            prompt = self.get_analysis_prompt(call)
            
            # Try different models based on preference
            result = None
            used_model = None
            
            if model_preference == "claude":
                result, used_model = await self.analyze_with_claude(prompt)
            elif model_preference == "gemini":
                result, used_model = await self.analyze_with_gemini(prompt)
            elif model_preference == "gpt":
                result, used_model = await self.analyze_with_gpt(prompt)
            
            if result:
                # Map score to tier
                score = result.get('score', 1)
                if score >= 8:
                    tier = 'ALPHA'
                elif score >= 6:
                    tier = 'SOLID'
                elif score >= 4:
                    tier = 'BASIC'
                else:
                    tier = 'TRASH'
                
                # Update database
                update_data = {
                    'analysis_score': score,
                    'analysis_model': used_model,
                    'analysis_legitimacy_factor': result.get('legitimacy_factor', ''),
                    'analysis_tier': tier,
                    'analysis_description': result.get('explanation', ''),
                    'analysis_reanalyzed_at': datetime.utcnow().isoformat()
                }
                
                self.supabase.table('crypto_calls') \
                    .update(update_data) \
                    .eq('krom_id', call['krom_id']) \
                    .execute()
                
                print(f"✓ Score: {score}/10 ({tier}) - {result.get('legitimacy_factor', '')}")
            else:
                print(f"✗ Analysis failed")

    async def analyze_tweets_batch(self, limit: int = 10, model_preference: str = "claude"):
        """Analyze tweets for calls"""
        print(f"Fetching {limit} calls with tweets for enhanced analysis...")
        
        # Get calls with tweets that need enhanced analysis
        calls = self.supabase.table('crypto_calls') \
            .select('krom_id, ticker, x_raw_tweets') \
            .is_('x_analysis_score', 'null') \
            .not_.is_('x_raw_tweets', 'null') \
            .limit(limit) \
            .execute()
        
        if not calls.data:
            print("No tweets need enhanced analysis")
            return
        
        print(f"Analyzing tweets for {len(calls.data)} calls...")
        
        for call in calls.data:
            tweets = call.get('x_raw_tweets', [])
            if not tweets:
                continue
                
            print(f"\nAnalyzing {len(tweets)} tweets for {call['ticker']}")
            
            # Get tweet analysis prompt
            prompt = self.get_tweet_analysis_prompt(call['ticker'], tweets)
            
            # Analyze based on preference
            result = None
            used_model = None
            
            if model_preference == "claude":
                result, used_model = await self.analyze_with_claude(prompt)
            elif model_preference == "gemini":
                result, used_model = await self.analyze_with_gemini(prompt)
            elif model_preference == "gpt":
                result, used_model = await self.analyze_with_gpt(prompt)
            
            if result:
                # Map score to tier
                score = result.get('score', 1)
                if score >= 8:
                    tier = 'ALPHA'
                elif score >= 6:
                    tier = 'SOLID'
                elif score >= 4:
                    tier = 'BASIC'
                else:
                    tier = 'TRASH'
                
                # Update database
                update_data = {
                    'x_analysis_score': score,
                    'x_analysis_model': used_model,
                    'x_best_tweet': result.get('best_tweet', ''),
                    'x_legitimacy_factor': result.get('legitimacy_factor', ''),
                    'x_analysis_tier': tier,
                    'x_analysis_summary': result.get('explanation', ''),
                    'x_reanalyzed_at': datetime.utcnow().isoformat()
                }
                
                self.supabase.table('crypto_calls') \
                    .update(update_data) \
                    .eq('krom_id', call['krom_id']) \
                    .execute()
                
                print(f"✓ Tweet Score: {score}/10 ({tier}) - {result.get('legitimacy_factor', '')}")
            else:
                print(f"✗ Tweet analysis failed")

async def main():
    analyzer = EnhancedCryptoAnalyzer()
    
    # Test with 10 calls first
    print("=== Testing Call Analysis with 10 calls ===")
    await analyzer.analyze_batch(limit=10, model_preference="claude")
    
    print("\n=== Testing Tweet Analysis with 10 calls ===")
    await analyzer.analyze_tweets_batch(limit=10, model_preference="claude")
    
    print("\n✓ Enhanced analysis complete!")
    print("Run with different models: --model gemini, --model gpt")
    print("Increase batch size: --batch 100")

if __name__ == "__main__":
    import asyncio
    import sys
    
    # Parse command line args
    model = "claude"
    batch_size = 10
    
    if "--model" in sys.argv:
        idx = sys.argv.index("--model")
        if idx + 1 < len(sys.argv):
            model = sys.argv[idx + 1]
    
    if "--batch" in sys.argv:
        idx = sys.argv.index("--batch")
        if idx + 1 < len(sys.argv):
            batch_size = int(sys.argv[idx + 1])
    
    analyzer = EnhancedCryptoAnalyzer()
    asyncio.run(analyzer.analyze_batch(limit=batch_size, model_preference=model))
    asyncio.run(analyzer.analyze_tweets_batch(limit=batch_size, model_preference=model))