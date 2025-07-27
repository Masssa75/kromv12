#!/usr/bin/env python3
"""Find decent legitimate projects - not unicorns like KEETA, but still way above average"""

import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv
from anthropic import Anthropic
import time
from datetime import datetime, timedelta

load_dotenv()

# Initialize
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
anthropic_key = os.getenv("ANTHROPIC_API_KEY")

supabase = create_client(url, key)
anthropic = Anthropic(api_key=anthropic_key)

print("Scanning for decent legitimate projects (not just KEETA-level)")
print("=" * 60)

# More realistic criteria
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

def process_batch(calls, batch_name):
    """Process a batch of calls"""
    decent_projects = []
    processed = 0
    
    print(f"\nProcessing {batch_name} ({len(calls)} calls)...")
    
    for i, call in enumerate(calls):
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
        
        # Progress
        if processed % 50 == 0:
            print(f"  Processed {processed} calls... Found {len(decent_projects)} decent projects so far")
            time.sleep(1)  # Rate limit
        
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
                best_feature = text.split("BEST:")[1].strip()
            
            # Lower threshold - anything 5+ is worth noting
            if score >= 5:
                decent_projects.append({
                    'ticker': call.get('ticker', 'Unknown'),
                    'score': score,
                    'best_feature': best_feature,
                    'date': call.get('created_at', '')[:10],
                    'original_ratings': f"C:{call.get('analysis_tier')} X:{call.get('x_analysis_tier')}",
                    'message_preview': message[:150] + '...'
                })
                
                # Print high scores immediately
                if score >= 7:
                    print(f"\n  🎯 FOUND (Score {score}): {call.get('ticker')} - {best_feature}")
        
        except Exception as e:
            continue
    
    print(f"  Completed: {processed} analyzed, {len(decent_projects)} decent projects found")
    return decent_projects

# Main execution
try:
    all_decent_projects = []
    
    # Process in time chunks to avoid timeout
    date_ranges = [
        ("Last week", datetime.now() - timedelta(days=7), datetime.now()),
        ("2 weeks ago", datetime.now() - timedelta(days=14), datetime.now() - timedelta(days=7)),
        ("3 weeks ago", datetime.now() - timedelta(days=21), datetime.now() - timedelta(days=14)),
        ("4 weeks ago", datetime.now() - timedelta(days=28), datetime.now() - timedelta(days=21)),
        ("5-6 weeks ago", datetime.now() - timedelta(days=42), datetime.now() - timedelta(days=28)),
        ("7-8 weeks ago", datetime.now() - timedelta(days=56), datetime.now() - timedelta(days=42))
    ]
    
    for period_name, start_date, end_date in date_ranges:
        # Get calls for this period
        result = supabase.table('crypto_calls') \
            .select('ticker, raw_data, analysis_tier, x_analysis_tier, created_at') \
            .gte('created_at', start_date.isoformat()) \
            .lt('created_at', end_date.isoformat()) \
            .limit(200) \
            .execute()
        
        if result.data:
            batch_results = process_batch(result.data, period_name)
            all_decent_projects.extend(batch_results)
        
        # Save progress
        with open('decent_projects_progress.json', 'w') as f:
            json.dump({
                'last_period': period_name,
                'total_found': len(all_decent_projects),
                'projects': all_decent_projects
            }, f, indent=2)
    
    # Final results
    print(f"\n{'='*60}")
    print("FINAL RESULTS")
    print(f"{'='*60}")
    print(f"Total decent projects found: {len(all_decent_projects)}")
    
    # Group by score
    high_score = [p for p in all_decent_projects if p['score'] >= 7]
    medium_score = [p for p in all_decent_projects if 5 <= p['score'] < 7]
    
    print(f"\nBreakdown:")
    print(f"  High legitimacy (7-10): {len(high_score)}")
    print(f"  Medium legitimacy (5-6): {len(medium_score)}")
    
    # Show top projects
    if high_score:
        print(f"\n{'='*60}")
        print("HIGH LEGITIMACY PROJECTS (Score 7+)")
        print(f"{'='*60}")
        
        for proj in sorted(high_score, key=lambda x: x['score'], reverse=True):
            print(f"\n{proj['ticker']} - Score: {proj['score']}")
            print(f"  Date: {proj['date']}")
            print(f"  Best feature: {proj['best_feature']}")
            print(f"  Original ratings: {proj['original_ratings']}")
            
            # Check if it was underrated
            if 'TRASH' in proj['original_ratings'] or 'BASIC' in proj['original_ratings']:
                print(f"  ⚠️  POTENTIALLY MISSED - was rated {proj['original_ratings']}")
    
    # Save final results
    output = {
        'scan_date': datetime.now().isoformat(),
        'total_found': len(all_decent_projects),
        'high_legitimacy': high_score,
        'medium_legitimacy': medium_score,
        'summary': {
            'high_count': len(high_score),
            'medium_count': len(medium_score),
            'underrated': len([p for p in high_score if 'TRASH' in p['original_ratings'] or 'BASIC' in p['original_ratings']])
        }
    }
    
    with open('decent_projects_final.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nFinal results saved to decent_projects_final.json")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()