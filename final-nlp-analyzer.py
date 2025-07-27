#!/usr/bin/env python3
"""Final NLP analyzer - processes calls safely with rate limiting"""

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

print("KROM Crypto Call Legitimacy Analysis")
print("=" * 60)
print("This script will analyze your crypto calls to find legitimate projects")
print("It processes 25 calls per minute to avoid rate limits")
print("=" * 60)

supabase = create_client(url, key)
anthropic = Anthropic(api_key=anthropic_key)

# Analysis prompt
PROMPT = """Analyze this crypto project announcement for legitimacy indicators:

{text}

Score 1-10 based on:
- Real product/utility described (not just price talk)
- Named people or companies mentioned
- Technical details or documentation
- Partnerships, audits, or funding mentioned

10 = Multiple strong indicators (like KEETA - real company, funding, named people)
7-9 = Some legitimate indicators
4-6 = Mixed signals
1-3 = Mostly hype/price focus

Format: SCORE:[X]|INDICATOR:[key finding in 10 words]"""

# Load previous results if any
results_file = 'final_nlp_results.json'
try:
    with open(results_file, 'r') as f:
        all_results = json.load(f)
    last_offset = all_results.get('last_offset', 0)
    projects = all_results.get('projects', [])
    print(f"Resuming from offset {last_offset} with {len(projects)} projects found...")
except:
    all_results = {'projects': [], 'last_offset': 0}
    projects = []
    last_offset = 0

# Process in batches
batch_size = 25  # Safe under 50/min limit
wait_time = 65   # Wait between batches

try:
    # Get total count
    count_result = supabase.table('crypto_calls').select('*', count='exact', head=True).execute()
    total_calls = count_result.count
    print(f"Total calls to analyze: {total_calls}")
    
    offset = last_offset
    
    while offset < total_calls:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Processing calls {offset}-{offset+batch_size}...")
        
        # Fetch batch
        result = supabase.table('crypto_calls') \
            .select('ticker, raw_data, analysis_tier, x_analysis_tier, created_at, krom_id') \
            .order('created_at', desc=True) \
            .range(offset, offset + batch_size - 1) \
            .execute()
        
        if not result.data:
            break
        
        batch_found = 0
        
        for call in result.data:
            raw = call.get('raw_data', {})
            if isinstance(raw, str):
                try:
                    raw = json.loads(raw)
                except:
                    continue
            
            text = raw.get('text', '')
            if len(text) < 40:
                continue
            
            # Truncate long messages
            text = text[:600]
            
            try:
                # Call AI
                resp = anthropic.messages.create(
                    model="claude-3-haiku-20240307",
                    max_tokens=100,
                    temperature=0,
                    messages=[{"role": "user", "content": PROMPT.format(text=text)}]
                )
                
                ai_response = resp.content[0].text
                
                # Parse
                score = 0
                indicator = ""
                
                if "SCORE:" in ai_response:
                    try:
                        score = float(ai_response.split("SCORE:")[1].split("|")[0].strip())
                    except:
                        continue
                
                if "INDICATOR:" in ai_response:
                    indicator = ai_response.split("INDICATOR:")[1].strip()[:100]
                
                # Save projects with score 5+
                if score >= 5:
                    project = {
                        'ticker': call.get('ticker'),
                        'score': score,
                        'indicator': indicator,
                        'date': call.get('created_at')[:10],
                        'original_ratings': f"C:{call.get('analysis_tier')} X:{call.get('x_analysis_tier')}",
                        'krom_id': call.get('krom_id')
                    }
                    projects.append(project)
                    batch_found += 1
                    
                    if score >= 8:
                        print(f"  🎯 HIGH LEGITIMACY: {project['ticker']} ({score}) - {indicator}")
                
            except Exception as e:
                if "rate_limit" in str(e):
                    print("  Rate limit hit! Waiting 90 seconds...")
                    time.sleep(90)
                    continue
        
        offset += len(result.data)
        
        # Save progress
        all_results = {
            'last_offset': offset,
            'total_analyzed': offset,
            'projects': projects,
            'last_update': datetime.now().isoformat()
        }
        
        with open(results_file, 'w') as f:
            json.dump(all_results, f, indent=2)
        
        # Progress update
        legitimate_count = len([p for p in projects if p['score'] >= 7])
        print(f"  Batch complete: Found {batch_found} legitimate projects")
        print(f"  Progress: {offset}/{total_calls} ({offset/total_calls*100:.1f}%)")
        print(f"  Total found: {len(projects)} (High legitimacy 7+: {legitimate_count})")
        
        # Wait before next batch
        if offset < total_calls:
            print(f"  Waiting {wait_time}s before next batch...")
            time.sleep(wait_time)
    
    # Final summary
    print(f"\n{'='*60}")
    print("ANALYSIS COMPLETE!")
    print(f"{'='*60}")
    print(f"Total calls analyzed: {offset}")
    print(f"Projects with legitimacy indicators (5+): {len(projects)}")
    
    # Score breakdown
    score_counts = {}
    for p in projects:
        s = int(p['score'])
        score_counts[s] = score_counts.get(s, 0) + 1
    
    print("\nScore distribution:")
    for score in sorted(score_counts.keys(), reverse=True):
        print(f"  Score {score}: {score_counts[score]} projects")
    
    # Top projects
    top_projects = sorted(projects, key=lambda x: x['score'], reverse=True)[:10]
    print(f"\nTop 10 most legitimate projects:")
    for p in top_projects:
        print(f"\n{p['ticker']} - Score {p['score']}/10")
        print(f"  Indicator: {p['indicator']}")
        print(f"  Date: {p['date']}")
        print(f"  Original: {p['original_ratings']}")
    
    # Save final results
    final_file = 'final_nlp_complete.json'
    with open(final_file, 'w') as f:
        json.dump({
            'analysis_date': datetime.now().isoformat(),
            'total_analyzed': offset,
            'legitimate_found': len(projects),
            'score_distribution': score_counts,
            'all_projects': projects
        }, f, indent=2)
    
    print(f"\n✅ Complete results saved to: {final_file}")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    print(f"\nPartial results saved in {results_file}")