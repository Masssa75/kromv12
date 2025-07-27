#!/usr/bin/env python3
"""
Run batch analysis on oldest calls from Supabase
"""

import os
import json
from datetime import datetime
from supabase import create_client
from anthropic import Anthropic
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Initialize clients
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Configure Gemini
gemini_key = os.getenv('GEMINI_API_KEY')
if gemini_key and '\n' in gemini_key:
    gemini_key = gemini_key.strip().split('\n')[-1]
genai.configure(api_key=gemini_key)
gemini = genai.GenerativeModel('gemini-pro')

def get_oldest_calls(limit=5):
    """Fetch the oldest calls from database"""
    print(f"Fetching {limit} oldest calls from Supabase...")
    
    # Get oldest calls that haven't been analyzed with new system
    result = supabase.table('crypto_calls') \
        .select('*') \
        .is_('analysis_score', 'null') \
        .not_.is_('raw_data', 'null') \
        .order('buy_timestamp', desc=False) \
        .limit(limit) \
        .execute()
    
    if not result.data:
        # If all have scores, get oldest regardless
        print("All calls have scores, fetching oldest for re-analysis...")
        result = supabase.table('crypto_calls') \
            .select('*') \
            .not_.is_('raw_data', 'null') \
            .order('buy_timestamp', desc=False) \
            .limit(limit) \
            .execute()
    
    print(f"Found {len(result.data)} calls")
    return result.data

def create_analysis_prompt(call):
    """Create prompt for call analysis"""
    raw_data = call.get('raw_data', {})
    ticker = call.get('ticker', 'Unknown')
    message = raw_data.get('text', 'No message')
    group = raw_data.get('group', {}).get('name', 'Unknown')
    
    # Get ROI if available for validation
    roi_5m = raw_data.get('roi_5m', 0)
    roi_1h = raw_data.get('roi_1h', 0)
    roi_24h = raw_data.get('roi_24h', 0)
    
    prompt = f"""Analyze this crypto call for legitimacy and potential value.

CRITICAL: Looking for tokens with major backing like:
- NOT/NOTCOIN: Binance backing, CZ tweet
- KEETA/KITA: $17M funding, ex-Google CEO investor

Call Details:
- Ticker: {ticker}
- Group: {group}
- Message: {message}

Historical Performance (for context):
- 5min ROI: {roi_5m}%
- 1hour ROI: {roi_1h}%
- 24hour ROI: {roi_24h}%

Score 1-10:
1-3: Shitcoin (just contract, no info)
4-7: Some legitimacy (small team/project)
8-10: Major backing (Binance, Google, major VCs)

Provide JSON only:
{{
  "score": <1-10>,
  "legitimacy_factor": "<1-6 words max>",
  "explanation": "<brief explanation>"
}}"""
    
    return prompt

def analyze_with_claude(prompt, model="claude-3-haiku-20240307"):
    """Analyze with Claude"""
    try:
        response = anthropic.messages.create(
            model=model,
            max_tokens=500,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = response.content[0].text
        # Extract JSON
        start = content.find('{')
        end = content.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(content[start:end])
        return json.loads(content)
        
    except Exception as e:
        print(f"Claude error: {e}")
        return None

def analyze_with_gemini(prompt):
    """Analyze with Gemini"""
    try:
        response = gemini.generate_content(prompt)
        content = response.text
        # Extract JSON
        start = content.find('{')
        end = content.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(content[start:end])
        return json.loads(content)
        
    except Exception as e:
        print(f"Gemini error: {e}")
        return None

def score_to_tier(score):
    """Convert score to tier"""
    if score >= 8:
        return 'ALPHA'
    elif score >= 6:
        return 'SOLID'
    elif score >= 4:
        return 'BASIC'
    else:
        return 'TRASH'

def analyze_batch(limit=5, model="claude-3-haiku"):
    """Run batch analysis on oldest calls"""
    print("\n=== KROM Historical Batch Analysis ===")
    print(f"Model: {model}")
    print(f"Batch size: {limit}")
    print("=" * 50)
    
    # Get oldest calls
    calls = get_oldest_calls(limit)
    
    if not calls:
        print("No calls to analyze")
        return
    
    results = []
    
    for i, call in enumerate(calls, 1):
        ticker = call.get('ticker', 'Unknown')
        krom_id = call.get('krom_id')
        buy_timestamp = call.get('buy_timestamp')
        
        print(f"\n[{i}/{limit}] Analyzing {ticker}")
        print(f"Call date: {buy_timestamp}")
        
        # Create prompt
        prompt = create_analysis_prompt(call)
        
        # Analyze based on model choice
        if model.startswith("claude"):
            result = analyze_with_claude(prompt, model)
        elif model == "gemini-pro":
            result = analyze_with_gemini(prompt)
        else:
            print(f"Unknown model: {model}")
            continue
        
        if result:
            score = result.get('score', 1)
            tier = score_to_tier(score)
            
            # Update database
            update_data = {
                'analysis_score': score,
                'analysis_model': model,
                'analysis_legitimacy_factor': result.get('legitimacy_factor', ''),
                'analysis_tier': tier,
                'analysis_description': result.get('explanation', ''),
                'analysis_reanalyzed_at': datetime.utcnow().isoformat() + 'Z'
            }
            
            supabase.table('crypto_calls') \
                .update(update_data) \
                .eq('krom_id', krom_id) \
                .execute()
            
            # Store result
            results.append({
                'token': ticker,
                'score': score,
                'tier': tier,
                'legitimacy_factor': result.get('legitimacy_factor', ''),
                'explanation': result.get('explanation', ''),
                'date': buy_timestamp,
                'roi_24h': call.get('raw_data', {}).get('roi_24h', 0)
            })
            
            print(f"✓ Score: {score}/10 ({tier})")
            print(f"✓ Legitimacy: {result.get('legitimacy_factor', '')}")
            print(f"✓ 24h ROI: {call.get('raw_data', {}).get('roi_24h', 0)}%")
            
        else:
            print("✗ Analysis failed")
    
    # Summary
    print("\n" + "=" * 50)
    print("ANALYSIS SUMMARY")
    print("=" * 50)
    
    if results:
        avg_score = sum(r['score'] for r in results) / len(results)
        print(f"Calls analyzed: {len(results)}")
        print(f"Average score: {avg_score:.1f}")
        print(f"Score distribution:")
        
        tiers = {'ALPHA': 0, 'SOLID': 0, 'BASIC': 0, 'TRASH': 0}
        for r in results:
            tiers[r['tier']] += 1
        
        for tier, count in tiers.items():
            print(f"  {tier}: {count}")
        
        print("\nDetailed results:")
        for r in results:
            print(f"\n{r['token']} - Score: {r['score']}/10 ({r['tier']})")
            print(f"Legitimacy: {r['legitimacy_factor']}")
            print(f"24h ROI: {r['roi_24h']}%")
            print(f"Analysis: {r['explanation'][:100]}...")

if __name__ == "__main__":
    # Run analysis on 5 oldest calls
    analyze_batch(limit=5, model="claude-3-haiku-20240307")