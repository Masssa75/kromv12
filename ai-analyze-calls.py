#!/usr/bin/env python3
"""AI-powered analysis of crypto calls to find hidden gems"""

import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv
from anthropic import Anthropic
from collections import defaultdict
import time

load_dotenv()

# Initialize clients
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")

supabase: Client = create_client(url, key)
anthropic = Anthropic(api_key=anthropic_key)

print("AI-Powered Crypto Call Analysis")
print("=" * 60)

# AI prompt for identifying high-value calls
ANALYSIS_PROMPT = """Analyze this crypto call message and identify signals of a potentially valuable opportunity.

Message: {message}

Look for ANY of these signals (not just keywords):
1. Endorsements or connections to influential people/companies (even indirect)
2. Strong technical fundamentals or innovation
3. Experienced team background (even if names aren't famous)
4. Significant funding or backing (even without specific amounts)
5. First-mover advantage or unique narrative
6. Strong community metrics or organic growth
7. Partnerships or integrations
8. Security features (audits, KYC, etc.)
9. Previous successful projects by the team
10. Institutional interest or smart money involvement

Rate the call's potential from 1-10 and list the specific signals found.
Be generous in identifying positive signals - we want to catch hidden gems.

Response format:
SCORE: [1-10]
SIGNALS: [bullet list of specific signals found]
SUMMARY: [one sentence summary of why this could be valuable]

If score is less than 5, just return:
SCORE: [1-10]
SKIP: Low potential
"""

def analyze_call_with_ai(message):
    """Use Claude to analyze a crypto call for hidden value signals"""
    try:
        response = anthropic.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=500,
            temperature=0.3,
            messages=[
                {
                    "role": "user",
                    "content": ANALYSIS_PROMPT.format(message=message)
                }
            ]
        )
        return response.content[0].text
    except Exception as e:
        print(f"AI error: {e}")
        return None

# Results storage
high_potential_calls = []
analyzed_count = 0

# We'll analyze a sample to demonstrate (full analysis would be expensive)
print("Fetching calls to analyze...")

try:
    # Get calls that were rated BASIC or TRASH but might have hidden value
    result = supabase.table('crypto_calls') \
        .select('ticker, raw_data, analysis_tier, x_analysis_tier, created_at, krom_id') \
        .in_('analysis_tier', ['BASIC', 'TRASH']) \
        .order('created_at', desc=True) \
        .limit(100) \
        .execute()
    
    print(f"Analyzing {len(result.data)} potentially underrated calls with AI...\n")
    
    for i, call in enumerate(result.data):
        if i > 0 and i % 10 == 0:
            print(f"Processed {i}/{len(result.data)} calls...")
            time.sleep(1)  # Rate limiting
        
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
            if not message or len(message) < 20:
                continue
            
            # Analyze with AI
            ai_analysis = analyze_call_with_ai(message)
            if not ai_analysis:
                continue
            
            analyzed_count += 1
            
            # Parse AI response
            lines = ai_analysis.strip().split('\n')
            score = 0
            signals = []
            summary = ""
            
            for line in lines:
                if line.startswith('SCORE:'):
                    try:
                        score = int(line.split(':')[1].strip())
                    except:
                        score = 0
                elif line.startswith('SIGNALS:'):
                    # Continue reading until we hit SUMMARY
                    continue
                elif line.startswith('SUMMARY:'):
                    summary = line.split(':', 1)[1].strip()
                elif line.startswith('SKIP:'):
                    break
                elif line.strip().startswith('•') or line.strip().startswith('-'):
                    signals.append(line.strip())
            
            if score >= 6:  # High potential calls
                high_potential_calls.append({
                    'ticker': call['ticker'],
                    'created_at': call['created_at'],
                    'original_ratings': f"Claude={call['analysis_tier']}, X={call['x_analysis_tier']}",
                    'ai_score': score,
                    'signals': signals,
                    'summary': summary,
                    'message_preview': message[:200] + '...',
                    'krom_id': call['krom_id']
                })
    
    # Display results
    print("\n" + "=" * 60)
    print("HIGH POTENTIAL CALLS FOUND BY AI")
    print("=" * 60)
    
    # Sort by AI score
    high_potential_calls.sort(key=lambda x: x['ai_score'], reverse=True)
    
    print(f"\nFound {len(high_potential_calls)} high-potential calls out of {analyzed_count} analyzed")
    
    for call in high_potential_calls[:10]:  # Top 10
        print(f"\n{call['ticker']} - AI Score: {call['ai_score']}/10")
        print(f"  Date: {call['created_at']}")
        print(f"  Original ratings: {call['original_ratings']}")
        print(f"  AI Summary: {call['summary']}")
        print("  Signals found:")
        for signal in call['signals']:
            print(f"    {signal}")
        print(f"  Message: {call['message_preview']}")
    
    # Save results
    with open('ai_hidden_gems_analysis.json', 'w') as f:
        json.dump({
            'total_analyzed': analyzed_count,
            'high_potential_found': len(high_potential_calls),
            'calls': high_potential_calls
        }, f, indent=2)
    
    print(f"\nDetailed results saved to ai_hidden_gems_analysis.json")
    
    # Show what kinds of signals AI found that keyword search would miss
    print("\n" + "=" * 60)
    print("SIGNALS AI FOUND (that keyword search would miss)")
    print("=" * 60)
    
    unique_signals = set()
    for call in high_potential_calls:
        for signal in call['signals']:
            # Extract the core insight
            if 'team' in signal.lower() and 'google' not in signal.lower():
                unique_signals.add("Experienced team without name-dropping")
            elif 'community' in signal.lower():
                unique_signals.add("Strong community metrics")
            elif 'narrative' in signal.lower():
                unique_signals.add("Unique narrative or first-mover")
            elif 'audit' in signal.lower() or 'security' in signal.lower():
                unique_signals.add("Security features mentioned")
            elif 'integrat' in signal.lower() or 'partner' in signal.lower():
                unique_signals.add("Partnerships without big names")
    
    for signal in unique_signals:
        print(f"• {signal}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()