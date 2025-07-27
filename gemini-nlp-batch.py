#!/usr/bin/env python3
"""Process tweets in batches of 1000 with Gemini NLP analysis"""

import json
import os
from supabase import create_client
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Initialize
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
gemini_key = os.getenv('GEMINI_API_KEY')

supabase = create_client(url, key)
genai.configure(api_key=gemini_key)
model = genai.GenerativeModel('gemini-1.5-pro')

print('Processing tweets in batches of 1000 for NLP analysis...')
print('=' * 80)

# Process in batches
batch_size = 1000
offset = 0
all_results = []

while offset < 4560:  # We know there are ~4560 calls
    print(f'\nProcessing batch starting at offset {offset}...')
    
    # Get batch of calls
    result = supabase.table('crypto_calls') \
        .select('ticker, x_raw_tweets, created_at, krom_id, analysis_tier, x_analysis_tier, raw_data') \
        .not_.is_('x_raw_tweets', 'null') \
        .range(offset, offset + batch_size - 1) \
        .execute()
    
    if not result.data:
        break
    
    print(f'Processing {len(result.data)} calls in this batch')
    
    # Process the data
    batch_data = []
    for call in result.data:
        x_tweets = call.get('x_raw_tweets', [])
        if not x_tweets:
            continue
            
        if isinstance(x_tweets, str):
            try:
                x_tweets = json.loads(x_tweets)
            except:
                continue
        
        # Also get the original message
        raw_data = call.get('raw_data', {})
        if isinstance(raw_data, str):
            try:
                raw_data = json.loads(raw_data)
            except:
                raw_data = {}
        
        ticker = call.get('ticker', 'Unknown')
        original_message = raw_data.get('text', '')[:500] if isinstance(raw_data, dict) else ''
        
        # Collect tweets
        tweet_texts = []
        for tweet in x_tweets:
            tweet_text = tweet.get('text', '') if isinstance(tweet, dict) else str(tweet)
            if len(tweet_text) > 20:
                tweet_texts.append(tweet_text[:300])  # Truncate to save space
        
        if tweet_texts:
            batch_data.append({
                'ticker': ticker,
                'original_message': original_message,
                'tweets': tweet_texts[:3],  # Max 3 tweets per project
                'date': call.get('created_at', '')[:10],
                'claude_rating': call.get('analysis_tier'),
                'x_rating': call.get('x_analysis_tier')
            })
    
    if not batch_data:
        offset += batch_size
        continue
    
    # Prepare prompt for this batch
    prompt = """You are an expert crypto analyst looking for legitimate projects similar to KEETA. 

KEETA EXAMPLE: Cross-border payments fintech with $17M funding from Eric Schmidt (ex-Google CEO), TechCrunch coverage, named founder Ty Schenk, real product with regulatory compliance.

TASK: Analyze these crypto projects using NLP to find GENUINE legitimacy indicators:

1. REAL FUNDING: Specific amounts, named investors, VC firms (e.g. "$10M Series A from Sequoia")
2. REAL COMPANIES: Verifiable partnerships (e.g. "partnership with Microsoft", not "backed by tech giants")
3. REAL PEOPLE: Named founders with backgrounds (e.g. "CEO John Smith, ex-Google engineer")
4. REAL PRODUCTS: Live apps, user metrics (e.g. "1M downloads on App Store", "50K daily active users")
5. REAL TRACTION: Press coverage, regulatory compliance (e.g. "featured in TechCrunch", "SEC approved")

IGNORE vague claims like:
- "backed by whales/insiders"
- "strong team" without names
- "huge partnership" without specifics
- Price/chart talk

Rate 1-10:
10 = KEETA-level (major funding, press, named team)
8-9 = Strong legitimacy (multiple verified claims)
6-7 = Some legitimate elements
1-5 = Mostly hype/speculation

PROJECTS:

"""

    # Add batch data
    for i, project in enumerate(batch_data):
        prompt += f"\n--- {i+1}. {project['ticker']} ---\n"
        prompt += f"Original announcement: {project['original_message']}\n"
        prompt += f"Twitter sentiment:\n"
        for j, tweet in enumerate(project['tweets']):
            prompt += f"- {tweet}\n"
    
    prompt += "\n\nReturn ONLY projects scoring 6+ as: TICKER|SCORE|SPECIFIC_REASONS"
    
    # Send to Gemini
    try:
        print(f'Sending batch to Gemini ({len(prompt):,} chars)...')
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0,
                max_output_tokens=4096,
            )
        )
        
        # Parse results
        batch_results = []
        for line in response.text.split('\n'):
            if '|' in line and not line.startswith('---'):
                parts = line.split('|')
                if len(parts) >= 3:
                    ticker = parts[0].strip()
                    try:
                        score = float(parts[1].strip())
                        reasons = '|'.join(parts[2:]).strip()
                        if score >= 6:
                            batch_results.append({
                                'ticker': ticker,
                                'score': score,
                                'reasons': reasons
                            })
                    except:
                        pass
        
        print(f'Found {len(batch_results)} legitimate projects in this batch')
        all_results.extend(batch_results)
        
        # Show batch results
        if batch_results:
            print('Batch findings:')
            for r in sorted(batch_results, key=lambda x: x['score'], reverse=True):
                print(f"  {r['ticker']}: {r['score']}/10 - {r['reasons'][:100]}...")
        
    except Exception as e:
        print(f'Error processing batch: {e}')
    
    offset += batch_size

# Save all results
print(f'\n{"="*80}')
print(f'FINAL RESULTS: Found {len(all_results)} legitimate projects total')
print('='*80)

# Sort by score
all_results.sort(key=lambda x: x['score'], reverse=True)

# Save to file
with open('/tmp/gemini_nlp_batch_results.json', 'w') as f:
    json.dump({
        'total_calls_analyzed': offset,
        'legitimate_found': len(all_results),
        'results': all_results
    }, f, indent=2)

print(f'\nResults saved to /tmp/gemini_nlp_batch_results.json')

# Show top findings
if all_results:
    print('\nTOP 10 MOST LEGITIMATE PROJECTS:')
    print('-' * 80)
    for i, result in enumerate(all_results[:10]):
        print(f"{i+1}. {result['ticker']} - Score: {result['score']}/10")
        print(f"   Reasons: {result['reasons']}")
        print()