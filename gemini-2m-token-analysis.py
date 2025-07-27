#!/usr/bin/env python3
"""Full dataset NLP analysis using Gemini 1.5 Pro's 2M token context window"""

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

# Use the latest stable version with 2M token context
model = genai.GenerativeModel('gemini-1.5-pro')

print('Gemini 1.5 Pro Analysis - Using Full 2M Token Context Window')
print('=' * 80)

# Get ALL calls with X data
print('Loading entire dataset...')
all_projects = []
offset = 0

while True:
    result = supabase.table('crypto_calls') \
        .select('ticker, x_raw_tweets, raw_data, analysis_tier, x_analysis_tier, created_at, krom_id') \
        .not_.is_('x_raw_tweets', 'null') \
        .order('created_at', desc=True) \
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
        
        # Extract all available information
        ticker = call.get('ticker', 'Unknown')
        announcement = raw_data.get('text', '') if isinstance(raw_data, dict) else ''
        
        # Get ALL tweets for comprehensive analysis
        tweet_texts = []
        for tweet in x_tweets:
            if isinstance(tweet, dict):
                text = tweet.get('text', '')
                if text and len(text) > 10:
                    tweet_texts.append(text)
        
        if announcement or tweet_texts:
            all_projects.append({
                'ticker': ticker,
                'id': call.get('krom_id'),
                'date': call.get('created_at', '')[:10],
                'announcement': announcement,
                'tweets': tweet_texts,
                'claude_rating': call.get('analysis_tier'),
                'x_rating': call.get('x_analysis_tier')
            })
    
    offset += len(result.data)
    print(f'Loaded {len(all_projects)} projects...')

print(f'\nTotal projects with data: {len(all_projects)}')

# Build the comprehensive prompt
prompt = """You are an expert crypto analyst with deep knowledge of legitimate blockchain projects. Your task is to identify genuine projects similar to KEETA from thousands of crypto calls.

KEETA GOLD STANDARD - What We're Looking For:
- Cross-border payments fintech solving real problems
- $17M Series A funding from Eric Schmidt (former Google CEO)
- Featured in TechCrunch, Forbes, and other major publications
- Named founder: Ty Schenk with verifiable background
- Live product with regulatory compliance (money transmitter licenses)
- Real office locations, employees on LinkedIn, company registration

YOUR TASK:
Analyze the following crypto projects using advanced NLP to identify GENUINE legitimacy indicators. You have both original announcements and Twitter/X sentiment data.

SCORING CRITERIA:

Score 10 (KEETA-level):
- Verifiable major funding (Series A/B/C) with named investors
- Coverage in mainstream press (TechCrunch, Forbes, WSJ, etc.)
- Named executives with LinkedIn profiles and proven backgrounds
- Live product with real users and regulatory compliance
- Company registration, office locations, employee listings

Score 8-9 (Strong legitimacy):
- At least $1M+ verifiable funding with investor names
- Real company with business registration
- Named team members with backgrounds
- Working product or clear development progress
- Some press coverage or institutional partnerships

Score 6-7 (Moderate legitimacy):
- Some verifiable elements (real team, product demo, small funding)
- Partnerships with known entities (must be specific)
- Legitimate business model beyond speculation
- Evidence of actual development work

Score 1-5 (Speculation/hype):
- No verifiable claims
- Anonymous teams
- Pure meme/community tokens
- Celebrity associations without business substance

CRITICAL ANALYSIS RULES:
1. Demand specificity: "backed by VCs" is meaningless without names
2. Verify claims: "ex-Google team" needs LinkedIn profiles
3. Distinguish hype from substance: high trading volume ≠ legitimacy
4. Look for red flags: anonymous teams, no product, pure speculation

IMPORTANT: Given that KEETA is extremely rare (1 in 100,000+ projects), be VERY critical. Expect to find perhaps 5-10 projects with score 6+, and maybe 1-2 with score 8+ across this entire dataset.

PROJECTS FOR ANALYSIS:

"""

# Add all projects with clear formatting
for i, project in enumerate(all_projects):
    prompt += f"\n{'='*70}\nPROJECT #{i+1}: {project['ticker']} (ID: {project['id']})\n"
    prompt += f"Date: {project['date']} | AI Ratings: Claude={project['claude_rating']}, X={project['x_rating']}\n\n"
    
    if project['announcement']:
        prompt += f"ORIGINAL ANNOUNCEMENT:\n{project['announcement']}\n\n"
    
    if project['tweets']:
        prompt += f"TWITTER/X SENTIMENT ({len(project['tweets'])} tweets):\n"
        for j, tweet in enumerate(project['tweets'], 1):
            prompt += f"{j}. {tweet}\n"
    prompt += "\n"

# Add query at the end as recommended in docs
prompt += """
========================================================================
FINAL ANALYSIS INSTRUCTIONS:

Based on your NLP analysis of all projects above, return ONLY those scoring 6 or higher.

Format each result as:
TICKER|SCORE|VERIFIABLE_EVIDENCE

Where VERIFIABLE_EVIDENCE must include specific names, amounts, companies, or facts that could be independently verified by a journalist.

Remember: Be extremely skeptical. Real projects like KEETA are extraordinarily rare in crypto.
"""

# Calculate token usage
prompt_chars = len(prompt)
estimated_tokens = prompt_chars // 4  # Rough estimate: 4 chars per token

print(f'\nPrompt statistics:')
print(f'- Total characters: {prompt_chars:,}')
print(f'- Estimated tokens: {estimated_tokens:,}')
print(f'- Using {estimated_tokens/2_097_152*100:.1f}% of 2M token limit')

if estimated_tokens > 2_000_000:
    print('\nERROR: Exceeds 2M token limit!')
    print('Need to reduce dataset size or split into batches')
    exit(1)

print('\nSending to Gemini 1.5 Pro for comprehensive NLP analysis...')
print('This will analyze all tweets and announcements in a single call.')
print('Processing may take 1-3 minutes...\n')

try:
    # Make the API call with full context
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0,
            max_output_tokens=8192,  # Maximum output
        )
    )
    
    print('='*80)
    print('COMPREHENSIVE NLP ANALYSIS COMPLETE')
    print('='*80)
    print('\nRaw response:')
    print(response.text)
    
    # Parse results
    results = []
    for line in response.text.split('\n'):
        if '|' in line and not any(x in line for x in ['=', '-', 'TICKER|SCORE']):
            parts = line.split('|', 2)  # Split into exactly 3 parts
            if len(parts) >= 3:
                try:
                    ticker = parts[0].strip()
                    score = float(parts[1].strip())
                    evidence = parts[2].strip()
                    results.append({
                        'ticker': ticker,
                        'score': score,
                        'evidence': evidence
                    })
                except:
                    pass
    
    # Save comprehensive results
    output = {
        'analysis_date': os.popen('date').read().strip(),
        'total_projects_analyzed': len(all_projects),
        'total_tweets_processed': sum(len(p['tweets']) for p in all_projects),
        'legitimate_projects_found': len(results),
        'results': sorted(results, key=lambda x: x['score'], reverse=True)
    }
    
    with open('gemini_comprehensive_nlp_results.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f'\n' + '='*80)
    print('ANALYSIS SUMMARY:')
    print(f'- Projects analyzed: {len(all_projects):,}')
    print(f'- Total tweets processed: {output["total_tweets_processed"]:,}')
    print(f'- Legitimate projects found (6+): {len(results)}')
    
    if results:
        print('\nTOP LEGITIMATE PROJECTS:')
        print('-'*80)
        for i, r in enumerate(sorted(results, key=lambda x: x['score'], reverse=True), 1):
            print(f"\n{i}. {r['ticker']} - Score: {r['score']}/10")
            print(f"   Evidence: {r['evidence'][:200]}{'...' if len(r['evidence']) > 200 else ''}")
        
        # Distribution
        score_dist = {}
        for r in results:
            score = int(r['score'])
            score_dist[score] = score_dist.get(score, 0) + 1
        
        print('\nScore Distribution:')
        for score in sorted(score_dist.keys(), reverse=True):
            print(f"  Score {score}: {score_dist[score]} projects")
    else:
        print('\nNo projects scored 6 or higher - this is expected given the rarity of legitimate projects.')
    
    print(f'\nFull results saved to: gemini_comprehensive_nlp_results.json')
    
except Exception as e:
    print(f'\nError during API call: {e}')
    print('\nTroubleshooting:')
    print('1. Check if your Gemini API key has access to gemini-1.5-pro')
    print('2. Ensure billing is enabled on your Google Cloud project')
    print('3. The free tier has strict limits - you need a paid account')
    print('4. Try the API key in Google AI Studio first to verify it works')
    
    import traceback
    traceback.print_exc()