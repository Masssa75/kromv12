#!/usr/bin/env python3
"""Scan calls that got SOLID or ALPHA ratings to see if AI identifies them as legitimate"""

import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

# Initialize
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")

supabase = create_client(url, key)
anthropic = Anthropic(api_key=anthropic_key)

print("Scanning high-rated calls to validate AI detection...")
print("=" * 60)

# Get calls rated SOLID or ALPHA by either system
result = supabase.table('crypto_calls') \
    .select('ticker, raw_data, analysis_tier, x_analysis_tier, created_at') \
    .or_('analysis_tier.in.(SOLID,ALPHA),x_analysis_tier.in.(SOLID,ALPHA)') \
    .order('created_at', desc=True) \
    .limit(30) \
    .execute()

print(f"Found {len(result.data)} SOLID/ALPHA rated calls to test\n")

PROMPT = """Analyze if this describes a legitimate crypto project with real backing:
{msg}

Look for: real company, funding, named people, credible partners, news coverage.
Rate 1-10 (10=very legitimate like a funded startup, 1=just hype)

Reply: SCORE:[1-10]|TYPE:[COMPANY/PRODUCT/MEMECOIN/UNCLEAR]|SIGNAL:[key indicator]"""

found_legitimate = []
tested = 0

for call in result.data:
    raw = call.get('raw_data', {})
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except:
            continue
    
    msg = raw.get('text', '')
    if len(msg) < 50:
        continue
    
    tested += 1
    ticker = call.get('ticker', 'Unknown')
    ratings = f"C:{call.get('analysis_tier')} X:{call.get('x_analysis_tier')}"
    
    print(f"Testing {ticker} ({ratings})...", end='', flush=True)
    
    try:
        resp = anthropic.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=100,
            temperature=0,
            messages=[{"role": "user", "content": PROMPT.format(msg=msg[:500])}]
        )
        
        text = resp.content[0].text
        
        # Parse
        score = 0
        proj_type = ""
        signal = ""
        
        parts = text.split("|")
        for part in parts:
            if "SCORE:" in part:
                try:
                    score = int(part.split(":")[1].strip())
                except:
                    pass
            elif "TYPE:" in part:
                proj_type = part.split(":", 1)[1].strip()
            elif "SIGNAL:" in part:
                signal = part.split(":", 1)[1].strip()
        
        print(f" AI Score: {score}")
        
        if score >= 7:
            found_legitimate.append({
                'ticker': ticker,
                'ai_score': score,
                'type': proj_type,
                'signal': signal,
                'original_ratings': ratings,
                'message_preview': msg[:150] + '...'
            })
            print(f"  ✓ LEGITIMATE: {signal}")
        
    except Exception as e:
        print(f" Error: {e}")

print(f"\n{'='*60}")
print(f"RESULTS: {len(found_legitimate)}/{tested} high-rated calls confirmed as legitimate")
print("=" * 60)

if found_legitimate:
    print("\nLegitimate projects found:")
    for proj in sorted(found_legitimate, key=lambda x: x['ai_score'], reverse=True):
        print(f"\n{proj['ticker']} - AI Score: {proj['ai_score']}/10")
        print(f"  Type: {proj['type']}")
        print(f"  Signal: {proj['signal']}")
        print(f"  Original: {proj['original_ratings']}")
else:
    print("\nNo legitimate projects found in SOLID/ALPHA calls!")
    print("This suggests either:")
    print("1. The AI criteria for 'legitimate' is too strict")
    print("2. Most SOLID/ALPHA calls are based on hype, not fundamentals")

# Now let's check some calls that were rated BASIC or TRASH
print(f"\n{'='*60}")
print("Now checking some BASIC/TRASH calls for missed gems...")
print("=" * 60)

# Get BASIC calls from 2 months ago (more likely to find gems)
result2 = supabase.table('crypto_calls') \
    .select('ticker, raw_data, analysis_tier, x_analysis_tier, created_at') \
    .in_('analysis_tier', ['BASIC', 'TRASH']) \
    .gte('created_at', '2025-05-15') \
    .lte('created_at', '2025-05-25') \
    .limit(30) \
    .execute()

print(f"Checking {len(result2.data)} older BASIC/TRASH calls...\n")

missed_gems = []

for call in result2.data[:30]:
    raw = call.get('raw_data', {})
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except:
            continue
    
    msg = raw.get('text', '')
    if len(msg) < 50:
        continue
    
    try:
        resp = anthropic.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=100,
            temperature=0,
            messages=[{"role": "user", "content": PROMPT.format(msg=msg[:500])}]
        )
        
        text = resp.content[0].text
        score = 0
        signal = ""
        
        parts = text.split("|")
        for part in parts:
            if "SCORE:" in part:
                try:
                    score = int(part.split(":")[1].strip())
                except:
                    pass
            elif "SIGNAL:" in part:
                signal = part.split(":", 1)[1].strip()
        
        if score >= 7:
            ticker = call.get('ticker', 'Unknown')
            print(f"🎯 MISSED GEM: {ticker} (Score: {score}) - {signal}")
            missed_gems.append({
                'ticker': ticker,
                'score': score,
                'signal': signal,
                'date': call.get('created_at', '')[:10],
                'original': f"C:{call.get('analysis_tier')} X:{call.get('x_analysis_tier')}"
            })
    
    except:
        continue

if missed_gems:
    print(f"\n{'='*60}")
    print(f"POTENTIALLY MISSED {len(missed_gems)} LEGITIMATE PROJECTS")
    for gem in missed_gems:
        print(f"\n{gem['ticker']} ({gem['date']})")
        print(f"  AI Score: {gem['score']} | Original: {gem['original']}")
        print(f"  Why legitimate: {gem['signal']}")

# Save all results
with open('legitimacy_analysis_results.json', 'w') as f:
    json.dump({
        'high_rated_confirmed': found_legitimate,
        'potentially_missed': missed_gems,
        'stats': {
            'high_rated_tested': tested,
            'high_rated_legitimate': len(found_legitimate),
            'basic_trash_scanned': len(result2.data),
            'missed_gems_found': len(missed_gems)
        }
    }, f, indent=2)

print(f"\nFull results saved to legitimacy_analysis_results.json")