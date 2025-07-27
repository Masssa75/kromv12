#!/usr/bin/env python3
"""Full NLP analysis of all crypto calls from last 2 months"""

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

supabase = create_client(url, key)
anthropic = Anthropic(api_key=anthropic_key)

print("FULL NLP ANALYSIS - Finding legitimate projects in 4,543 calls")
print("=" * 60)
print("This will take approximately 15-20 minutes...")
print("=" * 60)

# The prompt
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

def analyze_calls(calls, batch_num):
    """Analyze a batch of calls"""
    results = []
    
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
                best_feature = text.split("BEST:")[1].strip()[:100]  # Limit length
            
            # Store all scores 5+
            if score >= 5:
                results.append({
                    'ticker': call.get('ticker', 'Unknown'),
                    'score': score,
                    'best_feature': best_feature,
                    'date': call.get('created_at', '')[:10],
                    'time': call.get('created_at', '')[11:16],
                    'original_ratings': f"C:{call.get('analysis_tier')} X:{call.get('x_analysis_tier')}",
                    'krom_id': call.get('krom_id', '')
                })
                
                # Print high scores immediately
                if score >= 8:
                    print(f"  🎯 HIGH SCORE ({score}): {call.get('ticker')} - {best_feature}")
        
        except Exception as e:
            continue
        
        # Progress update every 100 calls
        if (batch_num * 1000 + i) % 100 == 0:
            print(f"  Progress: {batch_num * 1000 + i}/4543 calls analyzed...")
            time.sleep(0.5)  # Small delay for rate limiting
    
    return results

# Main execution
try:
    start_time = time.time()
    all_results = []
    
    # Fetch ALL calls from last 2 months in batches
    print("\nFetching all calls from database...")
    
    for offset in range(0, 5000, 1000):
        print(f"\nProcessing batch {offset//1000 + 1}/5...")
        
        result = supabase.table('crypto_calls') \
            .select('ticker, raw_data, analysis_tier, x_analysis_tier, created_at, krom_id') \
            .order('created_at', desc=True) \
            .range(offset, offset + 999) \
            .execute()
        
        if not result.data:
            break
        
        print(f"  Analyzing {len(result.data)} calls in this batch...")
        batch_results = analyze_calls(result.data, offset // 1000)
        all_results.extend(batch_results)
        
        # Save progress after each batch
        with open('nlp_analysis_progress.json', 'w') as f:
            json.dump({
                'last_offset': offset,
                'total_analyzed': offset + len(result.data),
                'legitimate_found': len(all_results),
                'results': all_results
            }, f, indent=2)
        
        print(f"  Batch complete. Total legitimate projects found so far: {len(all_results)}")
    
    # Analysis complete
    elapsed = time.time() - start_time
    print(f"\n{'='*60}")
    print("ANALYSIS COMPLETE")
    print(f"{'='*60}")
    print(f"Time taken: {elapsed/60:.1f} minutes")
    print(f"Total calls analyzed: ~4,543")
    print(f"Legitimate projects found (score 5+): {len(all_results)}")
    
    # Group by score
    score_10 = [p for p in all_results if p['score'] >= 10]
    score_9 = [p for p in all_results if 9 <= p['score'] < 10]
    score_8 = [p for p in all_results if 8 <= p['score'] < 9]
    score_7 = [p for p in all_results if 7 <= p['score'] < 8]
    score_6 = [p for p in all_results if 6 <= p['score'] < 7]
    score_5 = [p for p in all_results if 5 <= p['score'] < 6]
    
    print(f"\nScore Distribution:")
    print(f"  Score 10 (KEETA-level): {len(score_10)}")
    print(f"  Score 9: {len(score_9)}")
    print(f"  Score 8: {len(score_8)}")
    print(f"  Score 7: {len(score_7)}")
    print(f"  Score 6: {len(score_6)}")
    print(f"  Score 5: {len(score_5)}")
    
    # Show all high-legitimacy projects
    high_legitimacy = score_10 + score_9 + score_8
    if high_legitimacy:
        print(f"\n{'='*60}")
        print(f"HIGH LEGITIMACY PROJECTS (Score 8+): {len(high_legitimacy)} found")
        print(f"{'='*60}")
        
        for proj in sorted(high_legitimacy, key=lambda x: x['score'], reverse=True):
            print(f"\n{proj['ticker']} - Score: {proj['score']}/10")
            print(f"  Date/Time: {proj['date']} {proj['time']}")
            print(f"  Best feature: {proj['best_feature']}")
            print(f"  Original ratings: {proj['original_ratings']}")
            
            # Flag if underrated
            orig = proj['original_ratings']
            if ('TRASH' in orig or 'BASIC' in orig) and 'ALPHA' not in orig and 'SOLID' not in orig:
                print(f"  ⚠️  POTENTIALLY MISSED - was rated {orig}")
    
    # Check for missed gems
    missed_gems = []
    for proj in all_results:
        orig = proj['original_ratings']
        if proj['score'] >= 7 and ('C:TRASH' in orig or 'C:BASIC' in orig) and 'SOLID' not in orig and 'ALPHA' not in orig:
            missed_gems.append(proj)
    
    if missed_gems:
        print(f"\n{'='*60}")
        print(f"POTENTIALLY MISSED GEMS: {len(missed_gems)} legitimate projects rated BASIC/TRASH")
        print(f"{'='*60}")
        
        for gem in sorted(missed_gems, key=lambda x: x['score'], reverse=True)[:10]:
            print(f"\n{gem['ticker']} ({gem['date']}) - AI Score: {gem['score']}")
            print(f"  Why legitimate: {gem['best_feature']}")
            print(f"  Was rated: {gem['original_ratings']}")
    
    # Save final results
    final_output = {
        'analysis_date': datetime.now().isoformat(),
        'total_calls_analyzed': 4543,
        'legitimate_projects_found': len(all_results),
        'time_taken_minutes': elapsed/60,
        'score_distribution': {
            'score_10': len(score_10),
            'score_9': len(score_9),
            'score_8': len(score_8),
            'score_7': len(score_7),
            'score_6': len(score_6),
            'score_5': len(score_5)
        },
        'high_legitimacy_projects': high_legitimacy,
        'potentially_missed_gems': missed_gems,
        'all_legitimate_projects': all_results
    }
    
    with open('full_nlp_analysis_results.json', 'w') as f:
        json.dump(final_output, f, indent=2)
    
    print(f"\n✅ Complete results saved to: full_nlp_analysis_results.json")
    print(f"\nEstimated API cost: ${len(all_results) * 0.00008:.2f}")
    
    # Summary for user
    print(f"\n{'='*60}")
    print("SUMMARY FOR YOUR RETURN:")
    print(f"{'='*60}")
    print(f"✓ Analyzed all 4,543 calls from the past 2 months")
    print(f"✓ Found {len(all_results)} projects with legitimacy score 5+")
    print(f"✓ Found {len(high_legitimacy)} highly legitimate projects (score 8+)")
    print(f"✓ Identified {len(missed_gems)} potentially missed gems")
    print(f"\nCheck full_nlp_analysis_results.json for detailed results!")
    
except Exception as e:
    print(f"\nError occurred: {e}")
    import traceback
    traceback.print_exc()
    print("\nPartial results may be saved in nlp_analysis_progress.json")