#!/usr/bin/env python3
"""
Test enhanced crypto analysis with real data
"""

import os
import json
from datetime import datetime
from supabase import create_client
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

# Initialize clients
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

def test_call_analysis():
    """Test enhanced analysis on a few calls"""
    print("=== Testing Enhanced Call Analysis ===\n")
    
    # Get a few recent calls
    calls = supabase.table('crypto_calls') \
        .select('krom_id, ticker, raw_data') \
        .not_.is_('raw_data', 'null') \
        .limit(3) \
        .execute()
    
    if not calls.data:
        print("No calls found")
        return
    
    for call in calls.data:
        print(f"Analyzing {call['ticker']} (ID: {call['krom_id'][:8]}...)")
        
        # Create analysis prompt
        raw_data = call.get('raw_data', {})
        message_text = raw_data.get('text', 'No message')
        group_name = raw_data.get('group', {}).get('name', 'Unknown')
        
        prompt = f"""Analyze this crypto call for legitimacy and potential value. 

CRITICAL: This is for research purposes to identify truly valuable projects like:
- NOT/NOTCOIN: Backed by Binance, tweeted by CZ
- KEETA/KITA: $17M funding, ex-Google CEO as investor

Call Details:
- Ticker: {call.get('ticker', 'Unknown')}
- Message: {message_text}
- Group: {group_name}

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

        try:
            # Call Claude API
            response = anthropic.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=500,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Parse response
            result = json.loads(response.content[0].text)
            
            print(f"Score: {result['score']}/10")
            print(f"Legitimacy: {result['legitimacy_factor']}")
            print(f"Explanation: {result['explanation']}")
            print("-" * 50 + "\n")
            
        except Exception as e:
            print(f"Error: {e}")
            print("-" * 50 + "\n")

def test_tweet_analysis():
    """Test enhanced tweet analysis"""
    print("\n=== Testing Enhanced Tweet Analysis ===\n")
    
    # Get calls with tweets
    calls = supabase.table('crypto_calls') \
        .select('krom_id, ticker, x_raw_tweets') \
        .not_.is_('x_raw_tweets', 'null') \
        .limit(2) \
        .execute()
    
    if not calls.data:
        print("No calls with tweets found")
        return
    
    for call in calls.data:
        tweets = call.get('x_raw_tweets', [])
        if not tweets:
            continue
            
        print(f"Analyzing {len(tweets)} tweets for {call['ticker']}")
        
        # Create tweet texts
        tweet_texts = "\n\n".join([f"Tweet {i+1}: {t.get('text', '')}" for i, t in enumerate(tweets[:5])])
        
        prompt = f"""Analyze these tweets about {call['ticker']} crypto token for legitimacy signals.

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

        try:
            response = anthropic.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=700,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            
            result = json.loads(response.content[0].text)
            
            print(f"Score: {result['score']}/10")
            print(f"Legitimacy: {result['legitimacy_factor']}")
            print(f"Best Tweet: {result['best_tweet'][:100]}...")
            print(f"Explanation: {result['explanation']}")
            print("-" * 50 + "\n")
            
        except Exception as e:
            print(f"Error: {e}")
            print("-" * 50 + "\n")

if __name__ == "__main__":
    print("Testing Enhanced Crypto Analysis System")
    print("=" * 50)
    
    test_call_analysis()
    test_tweet_analysis()
    
    print("\nTest complete! Check results above.")
    print("To run full batch: python enhanced-crypto-analyzer.py --batch 10")