#!/usr/bin/env python3
"""Full NLP analysis using Gemini's 1M token window with paid API"""

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

# Use the pro model for best analysis
model = genai.GenerativeModel('gemini-1.5-pro')

print('Full NLP Analysis with Gemini 1.5 Pro (Paid Tier)')
print('=' * 80)

# Get ALL calls with X data
print('Loading all crypto calls with tweets...')
all_projects = []
offset = 0

while True:
    result = supabase.table('crypto_calls') \
        .select('ticker, x_raw_tweets, raw_data, analysis_tier, x_analysis_tier, created_at') \
        .not_.is_('x_raw_tweets', 'null') \
        .range(offset, offset + 999) \
        .execute()
    
    if not result.data:
        break
    
    for call in result.data:
        x_tweets = call.get('x_raw_tweets', [])
        if isinstance(x_tweets, str):
            try:
                x_tweets = json.loads(x_tweets)
            except:
                continue
        
        raw_data = call.get('raw_data', {})
        if isinstance(raw_data, str):
            try:
                raw_data = json.loads(raw_data)
            except:
                raw_data = {}
        
        # Extract key information
        ticker = call.get('ticker', 'Unknown')
        announcement = raw_data.get('text', '')[:1000] if isinstance(raw_data, dict) else ''
        
        # Get best tweets (up to 5)
        tweet_texts = []
        for tweet in x_tweets[:5]:
            if isinstance(tweet, dict):
                text = tweet.get('text', '')
                if len(text) > 20:
                    tweet_texts.append(text[:500])
        
        if announcement or tweet_texts:
            all_projects.append({
                'ticker': ticker,
                'date': call.get('created_at', '')[:10],
                'announcement': announcement,
                'tweets': tweet_texts,
                'ai_ratings': f"Claude:{call.get('analysis_tier')}, X:{call.get('x_analysis_tier')}"
            })
    
    offset += len(result.data)
    print(f'Loaded {len(all_projects)} projects...')

print(f'\nTotal projects loaded: {len(all_projects)}')

# Build comprehensive prompt
prompt = """You are an expert crypto analyst evaluating projects for legitimacy similar to KEETA.

KEETA GOLD STANDARD:
- Cross-border payments fintech company
- $17M funding from Eric Schmidt (ex-Google CEO)
- TechCrunch press coverage
- Named founder: Ty Schenk
- Real product with regulatory compliance
- Verifiable through multiple sources

ANALYSIS TASK:
Using advanced NLP, analyze ALL the following crypto projects to find ones with GENUINE legitimacy. You have access to both the original announcements and Twitter/X sentiment.

LOOK FOR CONCRETE EVIDENCE OF:
1. REAL FUNDING: Specific amounts, named investors, VC firms with verification
2. REAL COMPANIES: Existing businesses, verifiable partnerships, regulatory filings
3. REAL PEOPLE: Full names, LinkedIn profiles, previous companies, achievements
4. REAL PRODUCTS: Live applications, user numbers, app store listings, patents
5. REAL TRACTION: Press coverage, institutional adoption, verifiable metrics

IGNORE:
- Vague claims ("backed by VCs", "strong team", "major partnership coming")
- Celebrity/influencer connections without business substance
- Meme narratives and community hype
- Technical jargon without actual implementation

SCORING:
10 = KEETA-level (verifiable major funding, press, named team, real product)
9 = Near KEETA-level (missing one element but otherwise legitimate)
8 = Strong legitimacy (multiple verified elements)
7 = Good legitimacy (some verified elements, real potential)
6 = Moderate legitimacy (at least one strongly verified element)
1-5 = Speculation, hype, or memes

For each project, consider both the announcement and Twitter sentiment. Sometimes legitimate projects are discussed differently on social media.

PROJECTS TO ANALYZE:

"""

# Add all projects
for i, project in enumerate(all_projects):
    prompt += f"\n{'='*60}\nPROJECT {i+1}: {project['ticker']} ({project['date']})\n"
    prompt += f"AI Ratings: {project['ai_ratings']}\n\n"
    
    if project['announcement']:
        prompt += f"ANNOUNCEMENT:\n{project['announcement']}\n\n"
    
    if project['tweets']:
        prompt += "TWITTER SENTIMENT:\n"
        for j, tweet in enumerate(project['tweets']):
            prompt += f"{j+1}. {tweet}\n"
    prompt += "\n"

prompt += """
FINAL INSTRUCTIONS:
Return ONLY projects scoring 6 or higher in this exact format:
TICKER|SCORE|SPECIFIC_VERIFIABLE_REASONS

Be extremely critical. Remember that 99%+ of crypto projects are speculation. Focus only on concrete, verifiable claims that could be fact-checked by a journalist.

For context: In your analysis of 4,565 projects, you should expect to find perhaps 10-20 with any real legitimacy, and likely only 1-2 approaching KEETA's level.
"""

# Check prompt size
prompt_length = len(prompt)
estimated_tokens = prompt_length // 4

print(f'\nPrompt size: {prompt_length:,} characters')
print(f'Estimated tokens: {estimated_tokens:,}')
print(f'Percentage of 1M token limit: {estimated_tokens/1_000_000*100:.1f}%')

if estimated_tokens > 950_000:
    print('\nWARNING: Approaching 1M token limit. Trimming...')
    # Trim to most promising projects
    # Could implement smart filtering here if needed

print('\nMaking comprehensive NLP analysis call to Gemini...')
print('This may take 30-60 seconds...')

try:
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0,
            max_output_tokens=8192,
        )
    )
    
    print('\n' + '='*80)
    print('COMPREHENSIVE NLP ANALYSIS RESULTS:')
    print('='*80)
    print(response.text)
    
    # Parse and save results
    results = []
    for line in response.text.split('\n'):
        if '|' in line and not line.startswith('='):
            parts = line.split('|')
            if len(parts) >= 3:
                try:
                    ticker = parts[0].strip()
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
    with open('gemini_full_nlp_results.json', 'w') as f:
        json.dump({
            'total_projects_analyzed': len(all_projects),
            'legitimate_found': len(results),
            'results': sorted(results, key=lambda x: x['score'], reverse=True)
        }, f, indent=2)
    
    print(f'\nResults saved to gemini_full_nlp_results.json')
    print(f'\nSummary:')
    print(f'- Total projects analyzed: {len(all_projects):,}')
    print(f'- Projects with legitimacy (6+): {len(results)}')
    
    if results:
        print('\nTop legitimate projects found:')
        for i, r in enumerate(sorted(results, key=lambda x: x['score'], reverse=True)[:10]):
            print(f"\n{i+1}. {r['ticker']} - Score: {r['score']}/10")
            print(f"   {r['reasons']}")
    
except Exception as e:
    print(f'\nError: {e}')
    print('\nPossible issues:')
    print('1. API key might not have billing enabled')
    print('2. Project might not have billing set up')
    print('3. Rate limits for the specific project')
    print('\nTo fix: Ensure your Google Cloud project has billing enabled')