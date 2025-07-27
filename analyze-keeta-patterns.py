#!/usr/bin/env python3
"""Analyze crypto calls for KEETA-like patterns using AI"""

import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv
from anthropic import Anthropic
import time

load_dotenv()

# Initialize clients
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")

supabase: Client = create_client(url, key)
anthropic = Anthropic(api_key=anthropic_key)

print("Analyzing calls for KEETA-like patterns...")
print("=" * 60)

# KEETA-specific analysis prompt
KEETA_ANALYSIS_PROMPT = """Analyze this crypto call to determine if it has similar characteristics to KEETA (a legitimate fintech with $17M funding from Eric Schmidt).

Message: {message}

Look for these KEETA-like signals:
1. Real company/product (not just a memecoin)
2. Actual funding rounds with specific amounts (e.g., "$10M Series A")
3. Named founders or team members (not anonymous)
4. Credible investors or advisors (VCs, tech leaders, not just "Elon might tweet")
5. External validation (news articles, company websites, LinkedIn profiles)
6. Technical product or real utility described
7. Previous successful projects by the team

Score from 1-10 where:
- 9-10: Multiple strong signals like KEETA (real funding, named people, external proof)
- 7-8: Some legitimate signals but missing key elements
- 5-6: Possibly legitimate but needs more verification
- 1-4: Likely just hype/memecoin

Return ONLY this format:
SCORE: [number]
TICKER: [ticker if found]
KEY_SIGNALS: [most important signal found, max 100 chars]
VERDICT: [KEETA-LIKE, POSSIBLY, UNLIKELY]
"""

def analyze_call(message):
    """Analyze a single call for KEETA-like patterns"""
    try:
        response = anthropic.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=200,
            temperature=0.2,
            messages=[
                {
                    "role": "user",
                    "content": KEETA_ANALYSIS_PROMPT.format(message=message)
                }
            ]
        )
        return response.content[0].text
    except Exception as e:
        print(f"Error analyzing call: {e}")
        return None

# Fetch first 1000 calls
print("Fetching first 1000 calls from Supabase...")
try:
    result = supabase.table('crypto_calls') \
        .select('ticker, raw_data, analysis_tier, x_analysis_tier, created_at, krom_id') \
        .order('created_at', desc=True) \
        .limit(1000) \
        .execute()
    
    print(f"Retrieved {len(result.data)} calls")
    
    # Results storage
    keeta_like_calls = []
    possibly_keeta_like = []
    processed = 0
    
    print("\nAnalyzing calls...")
    print("-" * 60)
    
    for i, call in enumerate(result.data):
        raw_data = call.get('raw_data')
        if not raw_data:
            continue
            
        if isinstance(raw_data, str):
            try:
                raw_data = json.loads(raw_data)
            except:
                continue
        
        if isinstance(raw_data, dict):
            message = raw_data.get('text', '')
            if not message or len(message) < 30:
                continue
            
            # Progress indicator
            if processed > 0 and processed % 50 == 0:
                print(f"Processed {processed} calls... Found {len(keeta_like_calls)} KEETA-like projects")
                time.sleep(2)  # Rate limiting
            
            # Analyze with AI
            analysis = analyze_call(message)
            if not analysis:
                continue
            
            processed += 1
            
            # Parse response
            score = 0
            ticker = call.get('ticker', 'Unknown')
            key_signal = ""
            verdict = ""
            
            for line in analysis.strip().split('\n'):
                if line.startswith('SCORE:'):
                    try:
                        score = float(line.split(':')[1].strip())
                    except:
                        score = 0
                elif line.startswith('TICKER:'):
                    ticker = line.split(':', 1)[1].strip() or ticker
                elif line.startswith('KEY_SIGNALS:'):
                    key_signal = line.split(':', 1)[1].strip()
                elif line.startswith('VERDICT:'):
                    verdict = line.split(':')[1].strip()
            
            # Store results
            if verdict == "KEETA-LIKE" or score >= 8:
                keeta_like_calls.append({
                    'ticker': ticker,
                    'score': score,
                    'key_signal': key_signal,
                    'created_at': call['created_at'],
                    'original_ratings': f"Claude={call.get('analysis_tier', 'N/A')}, X={call.get('x_analysis_tier', 'N/A')}",
                    'message_preview': message[:150] + '...',
                    'krom_id': call.get('krom_id')
                })
                # Print immediately when found
                print(f"\n🎯 FOUND KEETA-LIKE: {ticker} (Score: {score})")
                print(f"   Signal: {key_signal}")
                print(f"   Original ratings: {call.get('analysis_tier', 'N/A')}/{call.get('x_analysis_tier', 'N/A')}")
                
            elif verdict == "POSSIBLY" or score >= 6:
                possibly_keeta_like.append({
                    'ticker': ticker,
                    'score': score,
                    'key_signal': key_signal,
                    'created_at': call['created_at']
                })
    
    # Final results
    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)
    print(f"Total calls processed: {processed}")
    print(f"KEETA-like projects found: {len(keeta_like_calls)}")
    print(f"Possibly KEETA-like: {len(possibly_keeta_like)}")
    
    # Sort by score
    keeta_like_calls.sort(key=lambda x: x['score'], reverse=True)
    
    # Display top KEETA-like calls
    if keeta_like_calls:
        print("\n" + "=" * 60)
        print("TOP KEETA-LIKE PROJECTS")
        print("=" * 60)
        
        for call in keeta_like_calls[:10]:
            print(f"\n{call['ticker']} - Score: {call['score']}/10")
            print(f"Date: {call['created_at']}")
            print(f"Key Signal: {call['key_signal']}")
            print(f"Original Ratings: {call['original_ratings']}")
            print(f"Message: {call['message_preview']}")
    
    # Save results
    results = {
        'total_processed': processed,
        'keeta_like': keeta_like_calls,
        'possibly_keeta_like': possibly_keeta_like[:20]  # Top 20 possibles
    }
    
    with open('keeta_pattern_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\nResults saved to keeta_pattern_results.json")
    
    # Cost estimate
    tokens_used = processed * 200  # Rough estimate
    cost = tokens_used * 0.25 / 1_000_000
    print(f"\nEstimated API cost: ${cost:.3f}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()