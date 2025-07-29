#!/usr/bin/env python3
"""Analyze 100 calls quickly"""

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

# Get offset from file if continuing
try:
    with open('nlp_offset.txt', 'r') as f:
        offset = int(f.read().strip())
except:
    offset = 0

print(f"Analyzing calls {offset} to {offset+100}...")

# Fetch 100 calls
result = supabase.table('crypto_calls') \
    .select('ticker, raw_data, analysis_tier, x_analysis_tier, created_at') \
    .order('created_at', desc=True) \
    .range(offset, offset + 99) \
    .execute()

PROMPT = """Rate legitimacy 1-10 (10=real company/funding, 1=pure hype):
{msg}

Reply: SCORE:[X]|REASON:[why in 10 words]"""

found = []
for call in result.data[:100]:
    raw = call.get('raw_data', {})
    if isinstance(raw, str):
        raw = json.loads(raw)
    
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
        reason = ""
        
        if "SCORE:" in text:
            score = float(text.split("SCORE:")[1].split("|")[0])
        if "REASON:" in text:
            reason = text.split("REASON:")[1].strip()
        
        if score >= 6:
            found.append({
                'ticker': call.get('ticker'),
                'score': score,
                'reason': reason,
                'original': f"{call.get('analysis_tier')}/{call.get('x_analysis_tier')}"
            })
    except:
        pass

# Results
print(f"\nProcessed 100 calls. Found {len(found)} with score 6+:")
for f in sorted(found, key=lambda x: x['score'], reverse=True):
    print(f"\n{f['ticker']} - Score: {f['score']}")
    print(f"  Why: {f['reason']}")
    print(f"  Original: {f['original']}")

# Save offset
with open('nlp_offset.txt', 'w') as f:
    f.write(str(offset + 100))

# Append to results file
try:
    with open('all_nlp_results.json', 'r') as f:
        all_results = json.load(f)
except:
    all_results = []

all_results.extend(found)
with open('all_nlp_results.json', 'w') as f:
    json.dump(all_results, f, indent=2)

print(f"\nTotal found so far: {len(all_results)}")
print(f"Next: Run again to analyze calls {offset+100} to {offset+200}")