#!/usr/bin/env python3
"""Working analyzer with proper prompts"""

import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv
from anthropic import Anthropic
import time

load_dotenv()

# Initialize
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")

supabase = create_client(url, key)
anthropic = Anthropic(api_key=anthropic_key)

print("Analyzing crypto project announcements for legitimacy indicators...")
print("=" * 60)

# Better prompt that frames it as analysis, not investment advice
ANALYSIS_PROMPT = """You are analyzing cryptocurrency project announcements to identify characteristics of legitimate vs hype-based projects for research purposes.

Announcement text:
{message}

Based on the announcement, identify legitimacy indicators:
- Does it mention real products or utilities?
- Are there named team members or companies?
- Is there mention of audits, partnerships, or funding?
- Does it focus on technology or just price?

Rate the legitimacy characteristics from 1-10 where:
10 = Multiple strong legitimacy indicators (like real funding, named teams, external validation)
7-9 = Some legitimacy indicators present
4-6 = Mixed signals
1-3 = Mostly hype-focused

Respond with: LEGITIMACY_SCORE:[1-10]|KEY_INDICATOR:[main positive or negative indicator]

This is for research into communication patterns, not investment advice."""

# Test with 10 calls first
print("Testing with 10 recent calls...")

result = supabase.table('crypto_calls') \
    .select('ticker, raw_data, analysis_tier, x_analysis_tier, created_at') \
    .order('created_at', desc=True) \
    .limit(10) \
    .execute()

legitimate_projects = []

for i, call in enumerate(result.data):
    raw = call.get('raw_data', {})
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except:
            continue
    
    message = raw.get('text', '')
    if len(message) < 30:
        continue
    
    ticker = call.get('ticker', 'Unknown')
    print(f"\n{i+1}. Analyzing {ticker}...")
    
    # Rate limiting - wait between calls
    if i > 0:
        time.sleep(1.5)
    
    try:
        response = anthropic.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=100,
            temperature=0,
            system="You are a researcher analyzing cryptocurrency project announcements to identify legitimacy patterns.",
            messages=[{"role": "user", "content": ANALYSIS_PROMPT.format(message=message[:500])}]
        )
        
        result_text = response.content[0].text
        print(f"   Response: {result_text[:100]}...")
        
        # Parse response
        score = 0
        indicator = ""
        
        if "LEGITIMACY_SCORE:" in result_text:
            try:
                score_part = result_text.split("LEGITIMACY_SCORE:")[1].split("|")[0]
                score = float(score_part.strip())
            except:
                pass
        
        if "KEY_INDICATOR:" in result_text:
            indicator_part = result_text.split("KEY_INDICATOR:")[1]
            indicator = indicator_part.strip()[:100]
        
        if score > 0:
            project_data = {
                'ticker': ticker,
                'legitimacy_score': score,
                'key_indicator': indicator,
                'original_ratings': f"Claude:{call.get('analysis_tier')} X:{call.get('x_analysis_tier')}",
                'date': call.get('created_at')[:10]
            }
            
            if score >= 6:
                legitimate_projects.append(project_data)
                print(f"   ✓ Legitimacy score: {score}/10")
                print(f"   Key indicator: {indicator}")
            else:
                print(f"   Score: {score}/10 (mostly hype)")
    
    except Exception as e:
        print(f"   Error: {str(e)[:100]}")
        if "rate_limit" in str(e):
            print("   Rate limit - waiting 60s...")
            time.sleep(60)

# Summary
print(f"\n{'='*60}")
print(f"TEST COMPLETE")
print(f"{'='*60}")
print(f"Analyzed {len(result.data)} calls")
print(f"Found {len(legitimate_projects)} with legitimacy indicators (score 6+)")

if legitimate_projects:
    print("\nProjects with legitimacy indicators:")
    for proj in sorted(legitimate_projects, key=lambda x: x['legitimacy_score'], reverse=True):
        print(f"\n{proj['ticker']} - Legitimacy Score: {proj['legitimacy_score']}/10")
        print(f"  Key indicator: {proj['key_indicator']}")
        print(f"  Original ratings: {proj['original_ratings']}")
        print(f"  Date: {proj['date']}")

# Save test results
with open('legitimacy_test_results.json', 'w') as f:
    json.dump({
        'test_size': len(result.data),
        'legitimate_found': len(legitimate_projects),
        'projects': legitimate_projects
    }, f, indent=2)

print(f"\nResults saved to legitimacy_test_results.json")
print("\nThis approach seems to work! Ready to scale up to full analysis.")