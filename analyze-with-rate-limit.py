#!/usr/bin/env python3
"""Analyze calls respecting 50/minute rate limit"""

import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv
from anthropic import Anthropic
import time
from datetime import datetime

load_dotenv()

# Initialize
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")

supabase = create_client(url, key)
anthropic = Anthropic(api_key=anthropic_key)

print("Analyzing calls with rate limit (50/minute)...")
print("This will take longer but won't hit limits")
print("=" * 60)

# Get calls
print("Fetching recent calls...")
result = supabase.table('crypto_calls') \
    .select('ticker, raw_data, analysis_tier, x_analysis_tier, created_at') \
    .order('created_at', desc=True) \
    .limit(500) \
    .execute()

print(f"Got {len(result.data)} calls to analyze")

PROMPT = """Rate this crypto project's legitimacy 1-10:
{msg}

10 = Real company with funding/major backers
7-9 = Legitimate project with verification
4-6 = Has potential, some real elements  
1-3 = Pure hype/meme

Reply: SCORE:[X]|WHY:[reason in 10 words max]"""

legitimate = []
processed = 0
start_time = time.time()

# Process 40 calls per minute (leaving buffer)
batch_size = 40
wait_time = 60  # seconds

for batch_start in range(0, len(result.data), batch_size):
    batch_end = min(batch_start + batch_size, len(result.data))
    batch = result.data[batch_start:batch_end]
    
    print(f"\nProcessing batch {batch_start//batch_size + 1} (calls {batch_start}-{batch_end})...")
    batch_found = 0
    
    for call in batch:
        raw = call.get('raw_data', {})
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except:
                continue
        
        msg = raw.get('text', '')[:400]
        if len(msg) < 50:
            continue
        
        try:
            resp = anthropic.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=80,
                temperature=0,
                messages=[{"role": "user", "content": PROMPT.format(msg=msg)}]
            )
            
            text = resp.content[0].text
            score = 0
            why = ""
            
            if "SCORE:" in text:
                try:
                    score = float(text.split("SCORE:")[1].split("|")[0])
                except:
                    pass
            if "WHY:" in text:
                why = text.split("WHY:")[1].strip()
            
            processed += 1
            
            if score >= 6:
                info = {
                    'ticker': call.get('ticker'),
                    'score': score,
                    'why': why,
                    'date': call.get('created_at')[:10],
                    'original': f"C:{call.get('analysis_tier')} X:{call.get('x_analysis_tier')}"
                }
                legitimate.append(info)
                batch_found += 1
                
                if score >= 8:
                    print(f"  🎯 HIGH SCORE: {info['ticker']} ({score}) - {why}")
        
        except Exception as e:
            if "rate_limit" in str(e):
                print("  Hit rate limit - waiting...")
                time.sleep(wait_time)
            continue
    
    print(f"  Found {batch_found} legitimate projects in this batch")
    print(f"  Total so far: {len(legitimate)} legitimate out of {processed} processed")
    
    # Wait before next batch
    if batch_end < len(result.data):
        print(f"  Waiting {wait_time}s for rate limit...")
        time.sleep(wait_time)

# Summary
elapsed = time.time() - start_time
print(f"\n{'='*60}")
print(f"COMPLETE - Processed {processed} calls in {elapsed/60:.1f} minutes")
print(f"Found {len(legitimate)} legitimate projects (score 6+)")

if legitimate:
    # Sort by score
    legitimate.sort(key=lambda x: x['score'], reverse=True)
    
    print(f"\nTop 10 legitimate projects:")
    for p in legitimate[:10]:
        print(f"\n{p['ticker']} - Score: {p['score']}/10")
        print(f"  Why: {p['why']}")
        print(f"  Date: {p['date']}")
        print(f"  Original: {p['original']}")
        if 'TRASH' in p['original'] or 'BASIC' in p['original']:
            print(f"  ⚠️  Potentially missed!")

# Save
with open('rate_limited_results.json', 'w') as f:
    json.dump({
        'processed': processed,
        'found': len(legitimate),
        'projects': legitimate
    }, f, indent=2)

print(f"\nSaved to rate_limited_results.json")