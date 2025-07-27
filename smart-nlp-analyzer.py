#!/usr/bin/env python3
"""Smart NLP analyzer that handles rate limits and saves progress"""

import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv
from anthropic import Anthropic
import time
from datetime import datetime
import sys

load_dotenv()

# Initialize
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")

supabase = create_client(url, key)
anthropic = Anthropic(api_key=anthropic_key)

# Load previous progress if exists
PROGRESS_FILE = 'nlp_analysis_progress.json'
RESULTS_FILE = 'nlp_complete_results.json'

try:
    with open(PROGRESS_FILE, 'r') as f:
        progress = json.load(f)
        last_offset = progress.get('last_offset', 0)
        all_results = progress.get('results', [])
        print(f"Resuming from offset {last_offset} with {len(all_results)} results found so far...")
except:
    last_offset = 0
    all_results = []
    print("Starting fresh analysis...")

print("=" * 60)
print("Smart NLP Analysis - Handles rate limits automatically")
print("Will analyze all 4,543 calls from your database")
print("=" * 60)

PROMPT = """Rate this crypto project's legitimacy 1-10:
{msg}

10 = Real company with funding/major backers (like KEETA)
7-9 = Legitimate project with some verification
4-6 = Has potential, some real elements  
1-3 = Pure hype/meme

Look for: real products, named teams, funding, audits, partnerships, technical details.

Reply: SCORE:[X]|WHY:[key reason in 10 words]"""

# Process in chunks of 30 (safe under 50/min limit)
BATCH_SIZE = 30
WAIT_BETWEEN_BATCHES = 45  # seconds

total_to_process = 4543
calls_processed = last_offset

while calls_processed < total_to_process:
    # Fetch next batch
    print(f"\nFetching calls {calls_processed} to {calls_processed + BATCH_SIZE}...")
    
    result = supabase.table('crypto_calls') \
        .select('ticker, raw_data, analysis_tier, x_analysis_tier, created_at, krom_id') \
        .order('created_at', desc=True) \
        .range(calls_processed, calls_processed + BATCH_SIZE - 1) \
        .execute()
    
    if not result.data:
        print("No more calls to process")
        break
    
    batch_start_time = time.time()
    batch_legitimate = 0
    
    for i, call in enumerate(result.data):
        raw = call.get('raw_data', {})
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except:
                continue
        
        msg = raw.get('text', '')
        if len(msg) < 50:
            continue
        
        # Truncate very long messages
        msg = msg[:500]
        
        try:
            # Make API call
            resp = anthropic.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=100,
                temperature=0,
                messages=[{"role": "user", "content": PROMPT.format(msg=msg)}]
            )
            
            text = resp.content[0].text
            
            # Parse response
            score = 0
            why = ""
            
            if "SCORE:" in text:
                try:
                    score_text = text.split("SCORE:")[1].split("|")[0].strip()
                    score = float(score_text)
                except:
                    continue
            
            if "WHY:" in text:
                why = text.split("WHY:")[1].strip()[:100]
            
            # Save all scores 5+
            if score >= 5:
                project = {
                    'ticker': call.get('ticker', 'Unknown'),
                    'score': score,
                    'why': why,
                    'date': call.get('created_at', '')[:10],
                    'time': call.get('created_at', '')[11:16],
                    'original_ratings': f"C:{call.get('analysis_tier')} X:{call.get('x_analysis_tier')}",
                    'krom_id': call.get('krom_id', ''),
                    'message_preview': msg[:100] + '...'
                }
                all_results.append(project)
                batch_legitimate += 1
                
                # Announce high scores
                if score >= 8:
                    print(f"  🎯 HIGH SCORE: {project['ticker']} ({score}) - {why}")
                    
        except Exception as e:
            if "rate_limit" in str(e):
                print(f"  Rate limit hit at call {i+1}/{len(result.data)}. Waiting 60s...")
                time.sleep(60)
                # Retry this call
                continue
            else:
                # Other error, skip this call
                pass
    
    calls_processed += len(result.data)
    
    # Batch complete - save progress
    progress = {
        'last_offset': calls_processed,
        'total_processed': calls_processed,
        'results': all_results,
        'last_update': datetime.now().isoformat()
    }
    
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)
    
    # Status update
    elapsed = time.time() - batch_start_time
    print(f"\nBatch complete in {elapsed:.1f}s")
    print(f"  Processed: {calls_processed}/{total_to_process} ({calls_processed/total_to_process*100:.1f}%)")
    print(f"  Found {batch_legitimate} legitimate projects in this batch")
    print(f"  Total legitimate found: {len(all_results)}")
    
    # Calculate high scores
    high_scores = len([r for r in all_results if r['score'] >= 7])
    if high_scores > 0:
        print(f"  High legitimacy (7+): {high_scores}")
    
    # Wait before next batch (if not done)
    if calls_processed < total_to_process:
        print(f"\nWaiting {WAIT_BETWEEN_BATCHES}s before next batch to avoid rate limits...")
        time.sleep(WAIT_BETWEEN_BATCHES)

# Analysis complete!
print(f"\n{'='*60}")
print("ANALYSIS COMPLETE!")
print(f"{'='*60}")
print(f"Total calls processed: {calls_processed}")
print(f"Legitimate projects found (5+): {len(all_results)}")

# Group by scores
score_dist = {}
for r in all_results:
    s = int(r['score'])
    score_dist[s] = score_dist.get(s, 0) + 1

print("\nScore distribution:")
for score in sorted(score_dist.keys(), reverse=True):
    print(f"  Score {score}: {score_dist[score]} projects")

# Find potentially missed gems
missed_gems = []
for r in all_results:
    if r['score'] >= 7 and ('C:TRASH' in r['original_ratings'] or 'C:BASIC' in r['original_ratings']):
        missed_gems.append(r)

if missed_gems:
    print(f"\n⚠️  Found {len(missed_gems)} potentially missed gems (high score but rated BASIC/TRASH)")
    print("\nTop missed gems:")
    for gem in sorted(missed_gems, key=lambda x: x['score'], reverse=True)[:5]:
        print(f"  {gem['ticker']} ({gem['date']}) - Score {gem['score']}")
        print(f"    Why: {gem['why']}")
        print(f"    Was rated: {gem['original_ratings']}")

# Save final results
final_output = {
    'analysis_complete': True,
    'analysis_date': datetime.now().isoformat(),
    'total_calls_processed': calls_processed,
    'legitimate_projects_found': len(all_results),
    'score_distribution': score_dist,
    'potentially_missed_gems': missed_gems,
    'all_results': sorted(all_results, key=lambda x: x['score'], reverse=True)
}

with open(RESULTS_FILE, 'w') as f:
    json.dump(final_output, f, indent=2)

print(f"\n✅ Complete results saved to: {RESULTS_FILE}")
print("\nTop 10 most legitimate projects found:")
for r in sorted(all_results, key=lambda x: x['score'], reverse=True)[:10]:
    print(f"\n{r['ticker']} - Score {r['score']}/10")
    print(f"  Why: {r['why']}")
    print(f"  Date: {r['date']} {r['time']}")
    print(f"  Original: {r['original_ratings']}")

print("\n🎉 Analysis complete! Enjoy your dinner!")