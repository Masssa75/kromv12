#!/usr/bin/env python3
"""Simple batch analyzer - processes 20 calls at a time"""

import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv
from anthropic import Anthropic
import time
import sys

load_dotenv()

# Initialize
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")

if not all([url, key, anthropic_key]):
    print("Missing environment variables!")
    sys.exit(1)

supabase = create_client(url, key)
anthropic = Anthropic(api_key=anthropic_key)

# Get batch number from command line
batch_num = int(sys.argv[1]) if len(sys.argv) > 1 else 0
offset = batch_num * 20

print(f"Processing batch {batch_num} (calls {offset}-{offset+19})...")

# Fetch 20 calls
result = supabase.table('crypto_calls') \
    .select('ticker, raw_data, analysis_tier, x_analysis_tier, created_at') \
    .order('created_at', desc=True) \
    .range(offset, offset + 19) \
    .execute()

if not result.data:
    print("No calls found")
    sys.exit(0)

print(f"Analyzing {len(result.data)} calls...")

PROMPT = """Rate crypto project legitimacy 1-10:
{msg}
Reply: SCORE:[X]|WHY:[reason max 10 words]"""

found = []

for i, call in enumerate(result.data):
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
            max_tokens=50,
            temperature=0,
            messages=[{"role": "user", "content": PROMPT.format(msg=msg)}]
        )
        
        text = resp.content[0].text
        score = 0
        why = ""
        
        if "SCORE:" in text and "|" in text:
            try:
                parts = text.split("|")
                score = float(parts[0].split(":")[1].strip())
                if len(parts) > 1 and "WHY:" in parts[1]:
                    why = parts[1].split(":")[1].strip()
            except:
                pass
        
        if score >= 5:
            found.append({
                'ticker': call.get('ticker'),
                'score': score,
                'why': why,
                'original': f"C:{call.get('analysis_tier')} X:{call.get('x_analysis_tier')}",
                'date': call.get('created_at')[:10]
            })
            
            if score >= 8:
                print(f"  🎯 HIGH SCORE: {call.get('ticker')} ({score}) - {why}")
    
    except Exception as e:
        if "rate_limit" in str(e):
            print("Rate limit hit, waiting 60s...")
            time.sleep(60)
        continue

print(f"\nBatch {batch_num} complete: Found {len(found)} legitimate projects")

# Save batch results
filename = f'batch_{batch_num}_results.json'
with open(filename, 'w') as f:
    json.dump({
        'batch': batch_num,
        'offset': offset,
        'processed': len(result.data),
        'found': found
    }, f, indent=2)

print(f"Results saved to {filename}")

# Show summary
if found:
    print("\nLegitimate projects in this batch:")
    for p in sorted(found, key=lambda x: x['score'], reverse=True):
        print(f"  {p['ticker']} - Score {p['score']} - {p['why']}")