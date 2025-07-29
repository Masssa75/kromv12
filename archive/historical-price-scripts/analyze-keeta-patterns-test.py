#!/usr/bin/env python3
"""Test version - Analyze 100 crypto calls for KEETA-like patterns"""

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

print("TEST RUN: Analyzing 100 calls for KEETA-like patterns...")
print("=" * 60)

# Simpler, faster prompt
KEETA_ANALYSIS_PROMPT = """Is this crypto call similar to KEETA (real fintech, $17M funding, Eric Schmidt investor)?

Message: {message}

Look for: real company, actual funding, named team, credible backers, news coverage.

Reply with ONLY:
SCORE: [1-10]
SIGNAL: [main reason, max 50 chars]
"""

def analyze_call(message):
    """Analyze a single call"""
    try:
        response = anthropic.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=100,
            temperature=0,
            messages=[{"role": "user", "content": KEETA_ANALYSIS_PROMPT.format(message=message[:500])}]  # Limit message length
        )
        return response.content[0].text
    except Exception as e:
        return None

# Fetch recent calls
print("Fetching 100 recent calls...")
try:
    result = supabase.table('crypto_calls') \
        .select('ticker, raw_data, analysis_tier, x_analysis_tier, created_at') \
        .order('created_at', desc=True) \
        .limit(100) \
        .execute()
    
    print(f"Retrieved {len(result.data)} calls")
    
    keeta_like = []
    processed = 0
    
    print("\nAnalyzing (this will take ~1-2 minutes)...")
    
    for call in result.data[:100]:  # Safety limit
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
            if len(message) < 30:
                continue
            
            # Rate limiting
            if processed > 0 and processed % 10 == 0:
                print(f"  Processed {processed}/100...")
                time.sleep(1)
            
            # Analyze
            analysis = analyze_call(message)
            if not analysis:
                continue
            
            processed += 1
            
            # Parse score
            score = 0
            signal = ""
            for line in analysis.strip().split('\n'):
                if line.startswith('SCORE:'):
                    try:
                        score = float(line.split(':')[1].strip())
                    except:
                        pass
                elif line.startswith('SIGNAL:'):
                    signal = line.split(':', 1)[1].strip()
            
            # High scores only
            if score >= 7:
                keeta_like.append({
                    'ticker': call.get('ticker', 'Unknown'),
                    'score': score,
                    'signal': signal,
                    'date': call['created_at'][:10],
                    'ratings': f"{call.get('analysis_tier', '?')}/{call.get('x_analysis_tier', '?')}",
                    'preview': message[:100] + '...'
                })
                print(f"\n✅ FOUND: {call.get('ticker')} - Score {score} - {signal}")
    
    print(f"\n{'='*60}")
    print(f"Processed: {processed} calls")
    print(f"Found: {len(keeta_like)} KEETA-like projects")
    
    if keeta_like:
        print("\nTop finds:")
        for item in sorted(keeta_like, key=lambda x: x['score'], reverse=True)[:5]:
            print(f"\n{item['ticker']} (Score: {item['score']})")
            print(f"  Signal: {item['signal']}")
            print(f"  Ratings: {item['ratings']}")
            print(f"  Preview: {item['preview']}")
    
    # Save
    with open('keeta_test_results.json', 'w') as f:
        json.dump({'processed': processed, 'found': keeta_like}, f, indent=2)
    
    print(f"\nCost: ~${processed * 0.00005:.3f}")
    
except Exception as e:
    print(f"Error: {e}")