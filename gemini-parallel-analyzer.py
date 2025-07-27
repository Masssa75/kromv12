#!/usr/bin/env python3
"""Ultra-fast parallel analyzer using Gemini AI with async processing"""

import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv
import google.generativeai as genai
import time
from datetime import datetime
import asyncio
import aiohttp
from typing import List, Dict, Optional
import sys

load_dotenv()

# Initialize
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
gemini_key = os.getenv("GEMINI_API_KEY")

if not gemini_key:
    print("ERROR: GEMINI_API_KEY not found in .env file!")
    sys.exit(1)

print("🚀 Ultra-Fast Parallel Analysis with Gemini AI")
print("=" * 60)
print("Processing 100 calls simultaneously (10 batches x 10 calls)")
print("=" * 60)

# Configure Gemini
genai.configure(api_key=gemini_key)

# We'll create multiple model instances for parallel processing
models = [genai.GenerativeModel('gemini-1.5-flash') for _ in range(10)]

supabase = create_client(url, key)

# Global results storage
all_results = []
processed_count = 0
start_time = time.time()

# Analysis prompt
PROMPT = """Analyze crypto announcement legitimacy (1-10):

{text}

10=Real company/funding, 7-9=Some legitimate signs, 4-6=Mixed, 1-3=Hype

Reply: SCORE:[X]|REASON:[main indicator, max 10 words]"""

async def analyze_call_async(call_data: Dict, model_index: int) -> Optional[Dict]:
    """Analyze a single call asynchronously"""
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
    text = text[:500]
    
    try:
        # Use async generation
        response = await asyncio.to_thread(
            models[model_index % len(models)].generate_content,
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
        
        processed_count += 1
        
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
            
            if score >= 8:
                print(f"  🎯 HIGH: {project['ticker']} ({score}) - {reason}")
            
            return project
        
    except Exception as e:
        if "quota" in str(e).lower():
            print("  ⚠️  Quota limit - waiting 10s...")
            await asyncio.sleep(10)
        return None

async def process_batch_async(batch: List[Dict], batch_index: int) -> List[Dict]:
    """Process a batch of calls concurrently"""
    tasks = []
    for i, call in enumerate(batch):
        # Distribute calls across different model instances
        model_index = (batch_index * 10 + i) % len(models)
        task = analyze_call_async(call, model_index)
        tasks.append(task)
    
    results = await asyncio.gather(*tasks)
    return [r for r in results if r is not None]

async def process_multiple_batches(calls: List[Dict], concurrent_batches: int = 10) -> None:
    """Process multiple batches concurrently"""
    global all_results
    
    batch_size = 10  # Each batch has 10 calls
    total_batches = (len(calls) + batch_size - 1) // batch_size
    
    for i in range(0, len(calls), batch_size * concurrent_batches):
        # Create up to 'concurrent_batches' batches
        batch_tasks = []
        
        for j in range(concurrent_batches):
            start_idx = i + j * batch_size
            end_idx = min(start_idx + batch_size, len(calls))
            
            if start_idx >= len(calls):
                break
                
            batch = calls[start_idx:end_idx]
            batch_index = (i + j * batch_size) // batch_size
            
            batch_tasks.append(process_batch_async(batch, batch_index))
        
        # Process all batches concurrently
        print(f"\nProcessing {len(batch_tasks)} batches ({len(batch_tasks) * batch_size} calls) in parallel...")
        batch_start = time.time()
        
        batch_results = await asyncio.gather(*batch_tasks)
        
        # Flatten results
        for batch_result in batch_results:
            all_results.extend(batch_result)
        
        batch_time = time.time() - batch_start
        calls_per_second = (len(batch_tasks) * batch_size) / batch_time
        
        # Progress update
        elapsed = time.time() - start_time
        legitimate = len([r for r in all_results if r['score'] >= 7])
        print(f"  Processed in {batch_time:.1f}s ({calls_per_second:.0f} calls/sec)")
        print(f"  Total: {processed_count}/{len(calls)} | Found: {len(all_results)} | High (7+): {legitimate}")
        print(f"  Overall speed: {processed_count/(elapsed/60):.0f} calls/minute")
        
        # Save progress
        save_progress()
        
        # Small delay between mega-batches to be nice to API
        await asyncio.sleep(0.5)

def save_progress():
    """Save current progress"""
    progress_data = {
        'total_processed': processed_count,
        'results': all_results,
        'last_update': datetime.now().isoformat()
    }
    
    with open('nlp_analysis_progress.json', 'w') as f:
        json.dump(progress_data, f, indent=2)
    
    with open('gemini_parallel_results.json', 'w') as f:
        json.dump(progress_data, f, indent=2)

async def main():
    """Main async function"""
    global all_results, processed_count
    
    try:
        print("Loading all calls from database...")
        
        # Load all calls
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
            
            if offset >= 4543:
                break
        
        print(f"Loaded {len(all_calls)} calls.")
        print(f"Starting parallel analysis (100 calls at once)...")
        
        # Process all calls
        await process_multiple_batches(all_calls, concurrent_batches=10)
        
        # Final summary
        elapsed = time.time() - start_time
        
        print(f"\n{'='*60}")
        print(f"🎉 ANALYSIS COMPLETE in {elapsed:.0f} seconds ({elapsed/60:.1f} minutes)!")
        print(f"{'='*60}")
        
        print(f"Total processed: {processed_count}")
        print(f"Average speed: {processed_count/elapsed:.1f} calls/second")
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
        
        # Potentially missed gems
        missed = [r for r in all_results if r['score'] >= 7 and 
                  ('TRASH' in r['original_ratings'] or 'BASIC' in r['original_ratings'])]
        
        if missed:
            print(f"\n⚠️  Found {len(missed)} potentially missed gems!")
            print("Top 5 missed:")
            for m in sorted(missed, key=lambda x: x['score'], reverse=True)[:5]:
                print(f"  {m['ticker']} (Score {m['score']}) - was rated {m['original_ratings']}")
        
        # Save final results
        save_progress()
        
        final_output = {
            'analysis_complete': True,
            'analysis_date': datetime.now().isoformat(),
            'total_processed': processed_count,
            'time_seconds': elapsed,
            'calls_per_second': processed_count/elapsed,
            'legitimate_found': len(all_results),
            'score_distribution': score_dist,
            'potentially_missed': missed,
            'all_results': sorted(all_results, key=lambda x: x['score'], reverse=True)
        }
        
        with open('gemini_final_results.json', 'w') as f:
            json.dump(final_output, f, indent=2)
        
        print(f"\n✅ Complete results saved!")
        print(f"View in browser: http://localhost:8080")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        save_progress()
        print("\nPartial results saved.")

if __name__ == "__main__":
    # Check if Gemini library is installed
    try:
        import google.generativeai
    except ImportError:
        print("Installing google-generativeai...")
        os.system("pip3 install google-generativeai")
        print("Please run the script again.")
        sys.exit(1)
    
    # Run the async main function
    asyncio.run(main())