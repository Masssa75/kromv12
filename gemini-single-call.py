#!/usr/bin/env python3
"""Single Gemini API call with condensed data to fit free tier limits"""

import json
import os
from supabase import create_client
from dotenv import load_dotenv
import google.generativeai as genai
import re

load_dotenv()

# Initialize
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
gemini_key = os.getenv('GEMINI_API_KEY')

supabase = create_client(url, key)
genai.configure(api_key=gemini_key)
model = genai.GenerativeModel('gemini-1.5-flash')  # Using flash for faster/cheaper

print('Preparing condensed data for single Gemini API call...')
print('=' * 80)

# First, do a pre-filter to find potentially legitimate projects
print('Pre-filtering for potentially legitimate projects...')

# Patterns that might indicate legitimacy
legitimacy_keywords = [
    r'\$\d+[MK]',  # Funding amounts
    r'Series [A-Z]',
    r'founder|CEO|CTO|co-founder',
    r'ex-(?:Google|Facebook|Amazon|Microsoft|Apple|Meta)',
    r'partnership with|backed by|funded by',
    r'\d+[MK]?\s*(?:users|downloads|customers)',
    r'TechCrunch|Forbes|Bloomberg',
    r'Y\s*Combinator|YC',
    r'Sequoia|a16z|Paradigm',
    r'live on.*app store|google play'
]

# Get all calls
all_calls = []
offset = 0
while offset < 4560:
    result = supabase.table('crypto_calls') \
        .select('ticker, x_raw_tweets, raw_data, analysis_tier, x_analysis_tier') \
        .not_.is_('x_raw_tweets', 'null') \
        .range(offset, offset + 999) \
        .execute()
    
    if not result.data:
        break
    
    all_calls.extend(result.data)
    offset += len(result.data)
    print(f'Loaded {len(all_calls)} calls...')

print(f'Total calls loaded: {len(all_calls)}')

# Pre-filter to find potentially legitimate projects
filtered_projects = []
for call in all_calls:
    x_tweets = call.get('x_raw_tweets', [])
    if isinstance(x_tweets, str):
        try:
            x_tweets = json.loads(x_tweets)
        except:
            continue
    
    raw_data = call.get('raw_data', {})
    if isinstance(raw_data, str):
        try:
            raw_data = json.loads(raw_data)
        except:
            raw_data = {}
    
    # Combine all text
    all_text = raw_data.get('text', '')[:500] if isinstance(raw_data, dict) else ''
    for tweet in x_tweets[:3]:
        if isinstance(tweet, dict):
            all_text += ' ' + tweet.get('text', '')[:200]
    
    # Check for legitimacy indicators
    has_indicators = False
    for pattern in legitimacy_keywords:
        if re.search(pattern, all_text, re.IGNORECASE):
            has_indicators = True
            break
    
    # Also include highly rated projects
    if has_indicators or call.get('analysis_tier') in ['ALPHA', 'SOLID'] or call.get('x_analysis_tier') in ['ALPHA', 'SOLID']:
        filtered_projects.append({
            'ticker': call.get('ticker'),
            'text': all_text[:800],  # Condensed text
            'ratings': f"Claude:{call.get('analysis_tier')}, X:{call.get('x_analysis_tier')}"
        })

print(f'Pre-filtered to {len(filtered_projects)} potentially legitimate projects')

# Further limit to fit in free tier (aim for ~25k tokens total)
# ~30 chars per token, so 25k tokens = 750k chars
# With prompt overhead, let's aim for 100 projects with 5k chars each = 500k chars
if len(filtered_projects) > 100:
    # Prioritize ALPHA/SOLID rated ones
    filtered_projects.sort(key=lambda x: (
        'ALPHA' in x['ratings'],
        'SOLID' in x['ratings']
    ), reverse=True)
    filtered_projects = filtered_projects[:100]

# Build single prompt
prompt = """Analyze these crypto projects to find legitimate ones like KEETA ($17M funding, Eric Schmidt, TechCrunch).

Score 1-10:
10 = Major funding, named investors, press coverage
8-9 = Verified metrics, known backers, real products  
6-7 = Some legitimate elements
1-5 = Mostly hype

Return ONLY 6+ scores as: TICKER|SCORE|REASONS

PROJECTS:
"""

for i, project in enumerate(filtered_projects):
    prompt += f"\n{i+1}. {project['ticker']} ({project['ratings']}): {project['text'][:400]}...\n"

prompt += "\n\nBe extremely critical. Focus on specific, verifiable claims only."

# Check size
print(f'Prompt size: {len(prompt):,} characters (~{len(prompt)//4:,} tokens)')

if len(prompt) > 120000:  # Stay well under limit
    print('Prompt too large, reducing...')
    prompt = prompt[:120000] + "\n\nBe extremely critical. Focus on specific, verifiable claims only."

# Single API call
print('Making single Gemini API call...')
try:
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0,
            max_output_tokens=2048,
        )
    )
    
    print('\n' + '='*80)
    print('GEMINI NLP ANALYSIS RESULTS:')
    print('='*80)
    print(response.text)
    
    # Parse results
    results = []
    for line in response.text.split('\n'):
        if '|' in line:
            parts = line.split('|')
            if len(parts) >= 3:
                try:
                    ticker = parts[0].strip()
                    score = float(parts[1].strip())
                    reasons = '|'.join(parts[2:]).strip()
                    if score >= 6:
                        results.append({
                            'ticker': ticker,
                            'score': score,
                            'reasons': reasons
                        })
                except:
                    pass
    
    print(f'\nFound {len(results)} legitimate projects')
    if results:
        print('\nTop findings:')
        for r in sorted(results, key=lambda x: x['score'], reverse=True)[:10]:
            print(f"- {r['ticker']}: {r['score']}/10 - {r['reasons']}")
    
except Exception as e:
    print(f'Error: {e}')