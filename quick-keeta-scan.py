#!/usr/bin/env python3
"""Quick scan for KEETA-like projects - processes in small batches"""

import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv
from anthropic import Anthropic
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

print("Quick KEETA scan - Processing 50 recent calls...")
print("=" * 60)

# Very focused prompt
PROMPT = """Check if this crypto call mentions a legitimate company (not memecoin):
{msg}

Reply: LEGIT:[YES/NO]|SCORE:[1-10]|WHY:[reason in 5 words]"""

# Get 50 recent calls
result = supabase.table('crypto_calls') \
    .select('ticker, raw_data, analysis_tier, x_analysis_tier, created_at') \
    .order('created_at', desc=True) \
    .limit(50) \
    .execute()

found = []
count = 0

for call in result.data:
    raw = call.get('raw_data', {})
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except:
            continue
    
    msg = raw.get('text', '')[:300]
    if len(msg) < 50:
        continue
    
    count += 1
    print(f"\r{count}/50 processed...", end='', flush=True)
    
    try:
        resp = anthropic.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=50,
            temperature=0,
            messages=[{"role": "user", "content": PROMPT.format(msg=msg)}]
        )
        
        text = resp.content[0].text
        
        # Quick parse
        if "LEGIT:YES" in text and "SCORE:" in text:
            score = 0
            why = ""
            
            parts = text.split("|")
            for part in parts:
                if "SCORE:" in part:
                    try:
                        score = int(part.split(":")[1].strip())
                    except:
                        pass
                elif "WHY:" in part:
                    why = part.split(":", 1)[1].strip()
            
            if score >= 7:
                found.append({
                    'ticker': call.get('ticker'),
                    'score': score,
                    'why': why,
                    'ratings': f"{call.get('analysis_tier')}/{call.get('x_analysis_tier')}",
                    'preview': msg[:100]
                })
    except:
        continue

print(f"\n\nFound {len(found)} legitimate projects:")
print("=" * 60)

for f in sorted(found, key=lambda x: x['score'], reverse=True):
    print(f"\n{f['ticker']} - Score: {f['score']}")
    print(f"Why: {f['why']}")
    print(f"Ratings: {f['ratings']}")
    print(f"Preview: {f['preview']}...")

# Save
with open('quick_keeta_results.json', 'w') as f:
    json.dump(found, f, indent=2)

print(f"\nSaved to quick_keeta_results.json")
print(f"Cost: ~${count * 0.00005:.3f}")