#!/usr/bin/env python3
"""Analyze Supabase calls directly for legitimacy"""

import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv
import re
from collections import defaultdict

load_dotenv()

# Initialize
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(url, key)

print("Analyzing 4,543 Supabase calls for legitimacy...")
print("=" * 60)

# Patterns to look for
funding_patterns = [
    r'\$\d+[MK]\s*(funding|raised|round|Series [A-Z])',
    r'Series [A-Z]\s*(round|funding)?',
    r'\d+\s*million\s*(dollar|usd|funding|raised)',
    r'seed\s*(round|funding|investment)',
    r'pre-?seed\s*(round|funding)',
]

company_patterns = [
    r'(Google|Microsoft|Amazon|Meta|Apple|Tesla|Coinbase|Binance|Sequoia|a16z|Paradigm)',
    r'(venture\s*capital|VC\s*backed|accelerator|Y\s*Combinator|YC)',
    r'(Fortune\s*500|Forbes|TechCrunch|Bloomberg)',
]

team_patterns = [
    r'(founder|co-?founder|CEO|CTO|CFO)\s+[A-Z][a-z]+\s+[A-Z][a-z]+',  # Named positions
    r'ex-?(Google|Facebook|Amazon|Microsoft|Apple|Coinbase)',
    r'team\s*(from|includes|consists)',
]

product_patterns = [
    r'(platform|protocol|infrastructure|solution|product)\s*(for|that|which)',
    r'(building|developing|creating)\s*(a|the)\s*(platform|protocol|product)',
    r'(mainnet|testnet|beta|alpha)\s*(launch|live|released)',
]

# Fetch all calls
print("Fetching all calls from Supabase...")
all_calls = []
offset = 0

while True:
    result = supabase.table('crypto_calls') \
        .select('*') \
        .order('created_at', desc=True) \
        .range(offset, offset + 999) \
        .execute()
    
    if not result.data:
        break
        
    all_calls.extend(result.data)
    offset += len(result.data)
    print(f"  Loaded {len(all_calls)} calls...")
    
    if len(all_calls) >= 4543:
        break

print(f"\nTotal calls loaded: {len(all_calls)}")

# Analyze each call
legitimate_calls = []

for i, call in enumerate(all_calls):
    if i % 500 == 0:
        print(f"Analyzing call {i}/{len(all_calls)}...")
    
    # Get the message text
    raw_data = call.get('raw_data')
    if not raw_data:
        continue
        
    if isinstance(raw_data, str):
        try:
            raw_data = json.loads(raw_data)
        except:
            continue
    
    text = raw_data.get('text', '') if isinstance(raw_data, dict) else str(raw_data)
    
    # Score based on patterns found
    score = 0
    indicators = []
    
    # Check funding mentions
    for pattern in funding_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            score += 3
            match = re.search(pattern, text, re.IGNORECASE)
            indicators.append(f"Funding: {match.group(0)}")
            break
    
    # Check company/investor mentions
    for pattern in company_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            score += 2
            match = re.search(pattern, text, re.IGNORECASE)
            indicators.append(f"Company/VC: {match.group(0)}")
            break
    
    # Check team mentions
    for pattern in team_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            score += 2
            match = re.search(pattern, text, re.IGNORECASE)
            indicators.append(f"Team: {match.group(0)[:30]}")
            break
    
    # Check product mentions
    for pattern in product_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            score += 1
            match = re.search(pattern, text, re.IGNORECASE)
            indicators.append(f"Product: {match.group(0)[:30]}")
            break
    
    # If score is high enough, save it
    if score >= 3:
        legitimate_calls.append({
            'ticker': call.get('ticker', 'Unknown'),
            'score': score,
            'indicators': indicators,
            'analysis_tier': call.get('analysis_tier'),
            'x_analysis_tier': call.get('x_analysis_tier'),
            'created_at': call.get('created_at'),
            'message_preview': text[:200] + '...',
            'krom_id': call.get('krom_id')
        })

# Sort by score
legitimate_calls.sort(key=lambda x: x['score'], reverse=True)

print(f"\n{'='*60}")
print(f"RESULTS: Found {len(legitimate_calls)} potentially legitimate projects")
print(f"{'='*60}")

# Show top 20
print("\nTop 20 most legitimate-looking projects:")
for i, proj in enumerate(legitimate_calls[:20]):
    print(f"\n{i+1}. {proj['ticker']} - Score: {proj['score']}")
    print(f"   Date: {proj['created_at'][:10]}")
    print(f"   Ratings: Claude={proj['analysis_tier']}, X={proj['x_analysis_tier']}")
    print(f"   Indicators: {', '.join(proj['indicators'])}")
    print(f"   Message: {proj['message_preview']}")

# Check for missed gems
missed_gems = [p for p in legitimate_calls if p['score'] >= 5 and 
               (p['analysis_tier'] in ['BASIC', 'TRASH'] or 
                p['x_analysis_tier'] in ['BASIC', 'TRASH'])]

if missed_gems:
    print(f"\n{'='*60}")
    print(f"POTENTIALLY MISSED GEMS: {len(missed_gems)} projects")
    print(f"{'='*60}")
    for gem in missed_gems[:10]:
        print(f"\n{gem['ticker']} - Score: {gem['score']}")
        print(f"  Was rated: Claude={gem['analysis_tier']}, X={gem['x_analysis_tier']}")
        print(f"  But found: {', '.join(gem['indicators'])}")

# Save results
with open('supabase_legitimacy_analysis.json', 'w') as f:
    json.dump({
        'total_analyzed': len(all_calls),
        'legitimate_found': len(legitimate_calls),
        'top_projects': legitimate_calls[:50],
        'missed_gems': missed_gems
    }, f, indent=2)

print(f"\nResults saved to supabase_legitimacy_analysis.json")