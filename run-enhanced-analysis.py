#!/usr/bin/env python3
"""
Run enhanced crypto analysis with available AI models
"""

import os
import json
from datetime import datetime
from supabase import create_client
from anthropic import Anthropic
import google.generativeai as genai
from dotenv import load_dotenv
import time

load_dotenv()

class EnhancedAnalyzer:
    def __init__(self):
        # Initialize Supabase
        self.supabase = create_client(
            os.getenv('SUPABASE_URL'),
            os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        )
        
        # Initialize available AI clients
        self.anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
        
        # Configure Gemini (handle duplicate keys)
        gemini_key = os.getenv('GEMINI_API_KEY')
        if gemini_key:
            # Split in case of duplicate keys and use the last one
            keys = gemini_key.strip().split('\n')
            genai.configure(api_key=keys[-1])
            self.gemini = genai.GenerativeModel('gemini-pro')
        else:
            self.gemini = None
    
    def analyze_calls(self, limit=10, use_model="claude"):
        """Analyze crypto calls with enhanced scoring"""
        print(f"\n=== Analyzing {limit} Calls with {use_model} ===\n")
        
        # Get calls without enhanced analysis
        calls = self.supabase.table('crypto_calls') \
            .select('*') \
            .is_('analysis_score', 'null') \
            .not_.is_('raw_data', 'null') \
            .limit(limit) \
            .execute()
        
        if not calls.data:
            # Try calls that were already analyzed to re-analyze with new system
            print("No new calls found, re-analyzing existing calls...")
            calls = self.supabase.table('crypto_calls') \
                .select('*') \
                .not_.is_('raw_data', 'null') \
                .not_.is_('analysis_tier', 'null') \
                .limit(limit) \
                .execute()
        
        if not calls.data:
            print("No calls found to analyze")
            return
        
        analyzed = 0
        for call in calls.data:
            ticker = call.get('ticker', 'Unknown')
            raw_data = call.get('raw_data', {})
            message = raw_data.get('text', 'No message')
            group = raw_data.get('group', {}).get('name', 'Unknown')
            
            print(f"\nAnalyzing: {ticker}")
            print(f"Group: {group}")
            print(f"Message preview: {message[:100]}...")
            
            prompt = self._create_call_prompt(ticker, message, group)
            
            try:
                if use_model == "claude":
                    result = self._analyze_with_claude(prompt)
                elif use_model == "gemini" and self.gemini:
                    result = self._analyze_with_gemini(prompt)
                else:
                    print(f"Model {use_model} not available")
                    continue
                
                if result:
                    # Calculate tier from score
                    score = result['score']
                    tier = self._score_to_tier(score)
                    
                    # Update database
                    update_data = {
                        'analysis_score': score,
                        'analysis_model': use_model,
                        'analysis_legitimacy_factor': result['legitimacy_factor'],
                        'analysis_tier': tier,
                        'analysis_description': result['explanation'],
                        'analysis_reanalyzed_at': datetime.utcnow().isoformat() + 'Z'
                    }
                    
                    self.supabase.table('crypto_calls') \
                        .update(update_data) \
                        .eq('krom_id', call['krom_id']) \
                        .execute()
                    
                    print(f"✓ Score: {score}/10 ({tier})")
                    print(f"✓ Legitimacy: {result['legitimacy_factor']}")
                    print(f"✓ Reason: {result['explanation'][:150]}...")
                    analyzed += 1
                    
                    # Small delay to avoid rate limits
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"✗ Error: {str(e)[:100]}")
        
        print(f"\n=== Analyzed {analyzed}/{len(calls.data)} calls ===")
    
    def analyze_tweets(self, limit=10, use_model="claude"):
        """Analyze tweets with enhanced scoring"""
        print(f"\n=== Analyzing Tweets for {limit} Calls with {use_model} ===\n")
        
        # Get calls with tweets
        calls = self.supabase.table('crypto_calls') \
            .select('krom_id, ticker, x_raw_tweets') \
            .is_('x_analysis_score', 'null') \
            .not_.is_('x_raw_tweets', 'null') \
            .limit(limit) \
            .execute()
        
        if not calls.data:
            print("Re-analyzing existing tweet analyses...")
            calls = self.supabase.table('crypto_calls') \
                .select('krom_id, ticker, x_raw_tweets') \
                .not_.is_('x_raw_tweets', 'null') \
                .not_.is_('x_analysis_tier', 'null') \
                .limit(limit) \
                .execute()
        
        if not calls.data:
            print("No tweets found to analyze")
            return
        
        analyzed = 0
        for call in calls.data:
            ticker = call.get('ticker', 'Unknown')
            tweets = call.get('x_raw_tweets', [])
            
            if not tweets:
                continue
            
            print(f"\nAnalyzing {len(tweets)} tweets for: {ticker}")
            
            prompt = self._create_tweet_prompt(ticker, tweets[:5])  # Analyze first 5 tweets
            
            try:
                if use_model == "claude":
                    result = self._analyze_with_claude(prompt, is_tweet=True)
                elif use_model == "gemini" and self.gemini:
                    result = self._analyze_with_gemini(prompt, is_tweet=True)
                else:
                    print(f"Model {use_model} not available")
                    continue
                
                if result:
                    score = result['score']
                    tier = self._score_to_tier(score)
                    
                    # Update database
                    update_data = {
                        'x_analysis_score': score,
                        'x_analysis_model': use_model,
                        'x_best_tweet': result.get('best_tweet', '')[:500],  # Limit length
                        'x_legitimacy_factor': result['legitimacy_factor'],
                        'x_analysis_tier': tier,
                        'x_analysis_summary': result['explanation'],
                        'x_reanalyzed_at': datetime.utcnow().isoformat() + 'Z'
                    }
                    
                    self.supabase.table('crypto_calls') \
                        .update(update_data) \
                        .eq('krom_id', call['krom_id']) \
                        .execute()
                    
                    print(f"✓ Tweet Score: {score}/10 ({tier})")
                    print(f"✓ Legitimacy: {result['legitimacy_factor']}")
                    print(f"✓ Best tweet: {result.get('best_tweet', '')[:100]}...")
                    analyzed += 1
                    
                    time.sleep(0.5)
                    
            except Exception as e:
                print(f"✗ Error: {str(e)[:100]}")
        
        print(f"\n=== Analyzed tweets for {analyzed}/{len(calls.data)} calls ===")
    
    def _create_call_prompt(self, ticker, message, group):
        """Create analysis prompt for calls"""
        return f"""Analyze this crypto call for legitimacy and potential value. 

CRITICAL: This is for research to identify truly valuable projects like:
- NOT/NOTCOIN: Backed by Binance, tweeted by CZ
- KEETA/KITA: $17M funding, ex-Google CEO as investor

Call Details:
- Ticker: {ticker}
- Message: {message}
- Group: {group}

Score on 1-10:
1-3: Complete shitcoin (just contract, no info)
4-7: Some legitimacy (unknown team, small company)
8-10: Major backing (Binance, Google, major VCs)

Provide JSON:
{{
  "score": <1-10>,
  "legitimacy_factor": "<1-6 words>",
  "explanation": "<brief explanation>"
}}

BE EXTREMELY SELECTIVE with 8+ scores. Look for REAL institutional backing."""
    
    def _create_tweet_prompt(self, ticker, tweets):
        """Create analysis prompt for tweets"""
        tweet_texts = "\n\n".join([f"Tweet {i+1}: {t.get('text', '')}" 
                                  for i, t in enumerate(tweets)])
        
        return f"""Analyze tweets about {ticker} for legitimacy signals.

LOOKING FOR tokens like:
- NOT/NOTCOIN: Binance backing, CZ tweet
- KEETA: Google investment, $17M funding

Tweets:
{tweet_texts}

Score 1-10:
1-3: Just spam/hype
4-7: Some project info
8-10: Major institutional backing

Provide JSON:
{{
  "score": <1-10>,
  "best_tweet": "<most legitimate tweet full text>",
  "legitimacy_factor": "<1-6 words>",
  "explanation": "<brief explanation>"
}}"""
    
    def _analyze_with_claude(self, prompt, is_tweet=False):
        """Use Claude for analysis"""
        try:
            response = self.anthropic.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=700 if is_tweet else 500,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Extract JSON from response
            content = response.content[0].text
            # Try to find JSON in the response
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = content[start:end]
                return json.loads(json_str)
            else:
                return json.loads(content)
                
        except Exception as e:
            print(f"Claude error: {e}")
            return None
    
    def _analyze_with_gemini(self, prompt, is_tweet=False):
        """Use Gemini for analysis"""
        try:
            response = self.gemini.generate_content(prompt)
            # Extract JSON from response
            content = response.text
            start = content.find('{')
            end = content.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = content[start:end]
                return json.loads(json_str)
            else:
                return json.loads(content)
                
        except Exception as e:
            print(f"Gemini error: {e}")
            return None
    
    def _score_to_tier(self, score):
        """Convert numeric score to tier"""
        if score >= 8:
            return 'ALPHA'
        elif score >= 6:
            return 'SOLID'
        elif score >= 4:
            return 'BASIC'
        else:
            return 'TRASH'

def main():
    import sys
    
    # Parse arguments
    batch_size = 10
    model = "claude"
    
    if "--batch" in sys.argv:
        idx = sys.argv.index("--batch")
        if idx + 1 < len(sys.argv):
            batch_size = int(sys.argv[idx + 1])
    
    if "--model" in sys.argv:
        idx = sys.argv.index("--model")
        if idx + 1 < len(sys.argv):
            model = sys.argv[idx + 1]
    
    print("Enhanced Crypto Analysis System")
    print("=" * 50)
    print(f"Batch size: {batch_size}")
    print(f"Model: {model}")
    
    analyzer = EnhancedAnalyzer()
    
    # Analyze calls
    analyzer.analyze_calls(limit=batch_size, use_model=model)
    
    # Analyze tweets
    analyzer.analyze_tweets(limit=batch_size, use_model=model)
    
    print("\n✓ Analysis complete!")
    print("\nUsage:")
    print("  python run-enhanced-analysis.py --batch 100 --model gemini")
    print("  python run-enhanced-analysis.py --batch 50 --model claude")

if __name__ == "__main__":
    main()