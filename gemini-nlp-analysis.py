#!/usr/bin/env python3
"""Use Gemini's 1M context window for NLP analysis of all tweets"""

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

print('Preparing comprehensive NLP analysis with Gemini 1.5 Pro...')
print('=' * 80)

# Get all calls with X data
print('Fetching all tweets from database...')
all_tweets_data = []
offset = 0

while True:
    result = supabase.table('crypto_calls') \
        .select('ticker, x_raw_tweets, created_at, krom_id, analysis_tier, x_analysis_tier') \
        .not_.is_('x_raw_tweets', 'null') \
        .range(offset, offset + 999) \
        .execute()
    
    if not result.data:
        break
    
    print(f'Processing batch {offset//1000 + 1}... ({len(result.data)} calls)')
    
    for call in result.data:
        x_tweets = call.get('x_raw_tweets', [])
        if not x_tweets:
            continue
            
        if isinstance(x_tweets, str):
            try:
                x_tweets = json.loads(x_tweets)
            except:
                continue
        
        ticker = call.get('ticker', 'Unknown')
        
        # Collect all tweets for this ticker
        tweet_texts = []
        for tweet in x_tweets:
            tweet_text = tweet.get('text', '') if isinstance(tweet, dict) else str(tweet)
            if len(tweet_text) > 20:  # Only substantial tweets
                tweet_texts.append(tweet_text)
        
        if tweet_texts:
            all_tweets_data.append({
                'ticker': ticker,
                'tweets': tweet_texts,
                'date': call.get('created_at', '')[:10],
                'claude_rating': call.get('analysis_tier'),
                'x_rating': call.get('x_analysis_tier')
            })
    
    offset += len(result.data)
    if offset >= 4560:
        break

print(f'Collected {len(all_tweets_data)} projects with tweet data')

# Prepare massive prompt for Gemini
prompt = """You are an expert crypto analyst looking for legitimate projects similar to KEETA. 

KEETA EXAMPLE: Cross-border payments fintech with $17M funding from Eric Schmidt (ex-Google CEO), TechCrunch coverage, named founder Ty Schenk, real product with regulatory compliance.

TASK: Analyze ALL the following crypto project tweets using natural language processing to identify the most legitimate projects. Look for:

1. REAL FUNDING: Actual funding amounts, named investors, VC firms
2. REAL COMPANIES: Partnerships with known companies (not just "backed by Meta")  
3. REAL PEOPLE: Named founders, executives with verifiable backgrounds
4. REAL PRODUCTS: Live apps, user metrics, regulatory compliance, partnerships
5. REAL TRACTION: Verifiable metrics, press coverage, institutional backing

IGNORE:
- Generic crypto marketing terms
- Vague claims without specifics
- Meme narratives and hype
- False pattern matches (like "meta" meaning market trend)

For each project, rate 1-10 where:
10 = KEETA-level legitimacy (real company, major funding, press coverage)
9-8 = Strong legitimacy indicators (verified metrics, known backers)
7-6 = Some legitimate elements (real product, named team)
5-4 = Mixed signals (claims that need verification)
3-1 = Pure speculation/memes

PROJECTS TO ANALYZE:

"""

# Add all projects to the prompt
for i, project in enumerate(all_tweets_data):
    prompt += f"\n--- PROJECT {i+1}: {project['ticker']} ({project['date']}) ---\n"
    prompt += f"Claude Rating: {project['claude_rating']}, X Rating: {project['x_rating']}\n"
    prompt += "TWEETS:\n"
    for j, tweet in enumerate(project['tweets'][:3]):  # Max 3 tweets per project
        prompt += f"{j+1}. {tweet}\n"
    prompt += "\n"

prompt += """

RETURN FORMAT:
For ONLY projects scoring 6+ (legitimate indicators), return:
[TICKER]|[SCORE]|[SPECIFIC_REASONS]

Focus on specific, verifiable claims. Be extremely critical - most crypto projects are hype.
"""

# Calculate token estimate
prompt_length = len(prompt)
estimated_tokens = prompt_length // 4  # Rough estimate: 4 chars per token

print(f'Prompt length: {prompt_length:,} characters')
print(f'Estimated tokens: {estimated_tokens:,}')

if estimated_tokens > 900000:
    print('WARNING: Prompt may exceed 1M token limit. Consider reducing data.')
    # Reduce to top-rated projects only
    legitimate_projects = [p for p in all_tweets_data if p['claude_rating'] in ['ALPHA', 'SOLID'] or p['x_rating'] in ['ALPHA', 'SOLID']]
    print(f'Reducing to {len(legitimate_projects)} top-rated projects only...')
    
    # Rebuild prompt with only legitimate projects
    prompt = prompt.split('PROJECTS TO ANALYZE:')[0] + "PROJECTS TO ANALYZE:\n\n"
    
    for i, project in enumerate(legitimate_projects):
        prompt += f"\n--- PROJECT {i+1}: {project['ticker']} ({project['date']}) ---\n"
        prompt += f"Claude Rating: {project['claude_rating']}, X Rating: {project['x_rating']}\n"
        prompt += "TWEETS:\n"
        for j, tweet in enumerate(project['tweets'][:3]):
            prompt += f"{j+1}. {tweet}\n"
        prompt += "\n"
    
    prompt += """

RETURN FORMAT:
For ONLY projects scoring 6+ (legitimate indicators), return:
[TICKER]|[SCORE]|[SPECIFIC_REASONS]

Focus on specific, verifiable claims. Be extremely critical - most crypto projects are hype.
"""

print(f'Sending to Gemini 1.5 Pro for NLP analysis...')

try:
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0,
            max_output_tokens=8192,
        )
    )
    
    print('\n' + '='*80)
    print('GEMINI NLP ANALYSIS RESULTS:')
    print('='*80)
    print(response.text)
    
    # Parse and save results
    results = []
    for line in response.text.split('\n'):
        if '|' in line and not line.startswith('---'):
            parts = line.split('|')
            if len(parts) >= 3:
                ticker = parts[0].strip()
                try:
                    score = float(parts[1].strip())
                    reasons = '|'.join(parts[2:]).strip()
                    results.append({
                        'ticker': ticker,
                        'score': score,
                        'reasons': reasons
                    })
                except:
                    pass
    
    # Save results
    with open('/tmp/gemini_nlp_results.json', 'w') as f:
        json.dump({
            'total_projects_analyzed': len(all_tweets_data),
            'legitimate_found': len(results),
            'results': sorted(results, key=lambda x: x['score'], reverse=True)
        }, f, indent=2)
    
    print(f'\nResults saved to /tmp/gemini_nlp_results.json')
    print(f'Found {len(results)} legitimate projects with scores 6+')
    
except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()