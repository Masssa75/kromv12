#!/usr/bin/env python3
"""Fast NLP analyzer using Gemini AI"""

import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv
import google.generativeai as genai
import time
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor
import threading

load_dotenv()

# Initialize
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
gemini_key = os.getenv("GEMINI_API_KEY")

print("Fast Analysis with Gemini AI")
print("=" * 60)

# Configure Gemini
genai.configure(api_key=gemini_key)
model = genai.GenerativeModel('gemini-1.5-flash')

supabase = create_client(url, key)

# Thread-safe results storage
results_lock = threading.Lock()
all_results = []
processed_count = 0

# Analysis prompt
PROMPT = """Analyze this crypto project announcement for legitimacy (1-10 scale):

{text}

Score based on:
- Real product/utility (not just hype)
- Named people/teams/companies
- Funding, audits, partnerships mentioned
- Technical details vs price focus

10 = KEETA-level (real company, major funding, named people)
7-9 = Some legitimate indicators
4-6 = Mixed signals
1-3 = Mostly hype

Reply ONLY: SCORE:[X]|REASON:[key indicator in 10 words max]"""

def analyze_call(call_data):
    """Analyze a single call with Gemini"""
    global processed_count
    
    raw = call_data.get('raw_data', {})
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except:
            return None
    
    text = raw.get('text', '')
    if len(text) < 40:
        return None
    
    # Truncate long messages
    text = text[:600]
    
    try:
        # Use Gemini (much faster than Claude)
        response = model.generate_content(
            PROMPT.format(text=text),
            generation_config=genai.types.GenerationConfig(
                temperature=0,
                max_output_tokens=50,
            )
        )
        
        result_text = response.text
        
        # Parse response
        score = 0
        reason = ""
        
        if "SCORE:" in result_text:
            try:
                score = float(result_text.split("SCORE:")[1].split("|")[0].strip())
            except:
                return None
        
        if "REASON:" in result_text:
            reason = result_text.split("REASON:")[1].strip()[:100]
        
        if score >= 5:
            project = {
                'ticker': call_data.get('ticker', 'Unknown'),
                'score': score,
                'reason': reason,
                'date': call_data.get('created_at', '')[:10],
                'time': call_data.get('created_at', '')[11:16],
                'original_ratings': f"C:{call_data.get('analysis_tier')} X:{call_data.get('x_analysis_tier')}",
                'krom_id': call_data.get('krom_id', '')
            }
            
            with results_lock:
                all_results.append(project)
                processed_count += 1
                
                if score >= 8:
                    print(f"🎯 HIGH SCORE: {project['ticker']} ({score}) - {reason}")
            
            return project
        
        with results_lock:
            processed_count += 1
        
    except Exception as e:
        if "quota" in str(e).lower():
            print("⚠️  Hit Gemini quota limit. Waiting 60s...")
            time.sleep(60)
        return None

def process_batch(calls):
    """Process a batch of calls in parallel"""
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(analyze_call, calls))
    return [r for r in results if r is not None]

def save_progress():
    """Save current progress"""
    with results_lock:
        progress_data = {
            'total_processed': processed_count,
            'results': all_results,
            'last_update': datetime.now().isoformat()
        }
    
    with open('nlp_analysis_progress.json', 'w') as f:
        json.dump(progress_data, f, indent=2)
    
    # Also save to Gemini-specific file
    with open('gemini_results.json', 'w') as f:
        json.dump(progress_data, f, indent=2)

# Main execution
try:
    print("Fetching all calls from database...")
    
    # Get all calls at once
    all_calls = []
    offset = 0
    
    while True:
        result = supabase.table('crypto_calls') \
            .select('ticker, raw_data, analysis_tier, x_analysis_tier, created_at, krom_id') \
            .order('created_at', desc=True) \
            .range(offset, offset + 999) \
            .execute()
        
        if not result.data:
            break
            
        all_calls.extend(result.data)
        offset += len(result.data)
        
        if offset >= 4543:  # We know the total
            break
    
    print(f"Loaded {len(all_calls)} calls. Starting fast analysis with Gemini...")
    print("Processing in batches of 50 with 10 parallel threads...")
    
    # Process in batches
    batch_size = 50
    start_time = time.time()
    
    for i in range(0, len(all_calls), batch_size):
        batch = all_calls[i:i + batch_size]
        batch_num = i // batch_size + 1
        
        print(f"\nBatch {batch_num}/{len(all_calls)//batch_size + 1}...")
        
        # Process batch in parallel
        batch_start = time.time()
        process_batch(batch)
        batch_time = time.time() - batch_start
        
        # Progress update
        with results_lock:
            legitimate = len([r for r in all_results if r['score'] >= 7])
            print(f"  Processed in {batch_time:.1f}s | Total: {processed_count}/{len(all_calls)} | Found: {len(all_results)} | High (7+): {legitimate}")
        
        # Save progress every batch
        save_progress()
        
        # Small delay between batches (Gemini is generous but let's be nice)
        time.sleep(0.5)
    
    # Final summary
    elapsed = time.time() - start_time
    
    print(f"\n{'='*60}")
    print(f"ANALYSIS COMPLETE in {elapsed/60:.1f} minutes!")
    print(f"{'='*60}")
    
    with results_lock:
        print(f"Total processed: {processed_count}")
        print(f"Legitimate projects found (5+): {len(all_results)}")
        
        # Score breakdown
        score_dist = {}
        for r in all_results:
            s = int(r['score'])
            score_dist[s] = score_dist.get(s, 0) + 1
        
        print("\nScore distribution:")
        for score in sorted(score_dist.keys(), reverse=True):
            print(f"  Score {score}: {score_dist[score]}")
        
        # Top projects
        top_projects = sorted(all_results, key=lambda x: x['score'], reverse=True)[:10]
        
        print("\nTop 10 most legitimate projects:")
        for p in top_projects:
            print(f"\n{p['ticker']} - Score {p['score']}/10")
            print(f"  Reason: {p['reason']}")
            print(f"  Date: {p['date']} {p['time']}")
            print(f"  Original: {p['original_ratings']}")
    
    # Save final results
    save_progress()
    
    final_output = {
        'analysis_complete': True,
        'analysis_date': datetime.now().isoformat(),
        'total_processed': processed_count,
        'time_minutes': elapsed/60,
        'legitimate_found': len(all_results),
        'score_distribution': score_dist,
        'all_results': sorted(all_results, key=lambda x: x['score'], reverse=True)
    }
    
    with open('gemini_final_results.json', 'w') as f:
        json.dump(final_output, f, indent=2)
    
    print(f"\n✅ Results saved to gemini_final_results.json")
    print(f"Processing speed: {processed_count/(elapsed/60):.0f} calls/minute")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    save_progress()
    print("\nPartial results saved.")