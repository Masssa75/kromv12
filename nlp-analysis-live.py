#!/usr/bin/env python3
"""Live NLP analysis with regular updates"""

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

print("Starting NLP Analysis - I'll update you every 100 calls!")
print("=" * 60)

ANALYSIS_PROMPT = """Rate this crypto project for legitimacy (not expecting KEETA-level):

{message}

Good signs (any of these):
- Mentions actual product/utility (not just "moon")
- Names any real people (team, advisors)
- References any real company/partnership
- Mentions audit, KYC, or doxxed team
- Describes technical features
- Links to docs/whitepaper/website
- Previous projects by team
- Organic community metrics

Bad signs:
- Only price predictions
- Just "LFG/moon/100x" hype
- Anonymous everything
- No actual product described

Rate 1-10 where:
10 = KEETA level (real funding, major backers)
7-9 = Legitimate project with some verification
4-6 = Has potential, some real elements
1-3 = Pure hype/meme

Format: SCORE:[X]|BEST:[best feature in 10 words]"""

# Process first 500 calls to start
print("\nFetching first 500 calls...")
result = supabase.table('crypto_calls') \
    .select('ticker, raw_data, analysis_tier, x_analysis_tier, created_at') \
    .order('created_at', desc=True) \
    .limit(500) \
    .execute()

print(f"Got {len(result.data)} calls. Starting analysis...\n")

legitimate_projects = []
processed = 0

for i, call in enumerate(result.data):
    raw_data = call.get('raw_data')
    if not raw_data:
        continue
        
    if isinstance(raw_data, str):
        try:
            raw_data = json.loads(raw_data)
        except:
            continue
    
    message = raw_data.get('text', '')
    if len(message) < 50:
        continue
    
    processed += 1
    
    try:
        response = anthropic.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=100,
            temperature=0,
            messages=[{"role": "user", "content": ANALYSIS_PROMPT.format(message=message[:500])}]
        )
        
        text = response.content[0].text
        
        # Parse
        score = 0
        best_feature = ""
        
        if "SCORE:" in text:
            try:
                score_part = text.split("SCORE:")[1].split("|")[0].strip()
                score = float(score_part)
            except:
                continue
        
        if "BEST:" in text:
            best_feature = text.split("BEST:")[1].strip()[:80]
        
        # Track all decent projects
        if score >= 5:
            project_info = {
                'ticker': call.get('ticker', 'Unknown'),
                'score': score,
                'best_feature': best_feature,
                'date': call.get('created_at', '')[:10],
                'original': f"C:{call.get('analysis_tier')} X:{call.get('x_analysis_tier')}"
            }
            legitimate_projects.append(project_info)
            
            # Announce high scores immediately
            if score >= 8:
                print(f"🎯 HIGH SCORE FOUND! {project_info['ticker']} - Score: {score}/10")
                print(f"   Why: {best_feature}")
                print(f"   Original ratings: {project_info['original']}\n")
    
    except Exception as e:
        continue
    
    # Update every 100 calls
    if processed % 100 == 0:
        high_score = len([p for p in legitimate_projects if p['score'] >= 7])
        print(f"UPDATE: Processed {processed} calls")
        print(f"  - Found {len(legitimate_projects)} legitimate projects (score 5+)")
        print(f"  - High legitimacy (7+): {high_score}")
        
        if high_score > 0:
            recent_high = [p for p in legitimate_projects if p['score'] >= 7][-3:]
            print("  Recent high-score finds:")
            for p in recent_high:
                print(f"    • {p['ticker']} ({p['score']}) - {p['best_feature'][:50]}...")
        print()
        
        # Small delay
        time.sleep(1)

# Final summary for first batch
print(f"\n{'='*60}")
print(f"FIRST BATCH COMPLETE - Processed {processed} calls")
print(f"{'='*60}")

if legitimate_projects:
    # Group by score
    score_dist = {}
    for p in legitimate_projects:
        s = int(p['score'])
        score_dist[s] = score_dist.get(s, 0) + 1
    
    print("Score distribution:")
    for score in sorted(score_dist.keys(), reverse=True):
        print(f"  Score {score}: {score_dist[score]} projects")
    
    # Show top projects
    top_projects = sorted(legitimate_projects, key=lambda x: x['score'], reverse=True)[:5]
    print(f"\nTop {len(top_projects)} projects found:")
    for p in top_projects:
        print(f"\n{p['ticker']} - Score: {p['score']}/10")
        print(f"  Date: {p['date']}")
        print(f"  Why legitimate: {p['best_feature']}")
        print(f"  Original rating: {p['original']}")
        if 'TRASH' in p['original'] or 'BASIC' in p['original']:
            print(f"  ⚠️  Potentially missed!")

# Save results
with open('nlp_first_batch_results.json', 'w') as f:
    json.dump({
        'processed': processed,
        'legitimate_found': len(legitimate_projects),
        'projects': legitimate_projects
    }, f, indent=2)

print(f"\nResults saved. Continue with more batches? (Would analyze remaining ~4000 calls)")