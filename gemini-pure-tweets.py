#!/usr/bin/env python3
"""Feed all tweets directly to Gemini for pure NLP analysis"""

import json
import os
from supabase import create_client
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

# Initialize
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
# Use the new Gemini API key with billing enabled
gemini_key = 'AIzaSyBFtSMQzyOZXYuHeLvJzu4bj8uIiBR_0DU'

supabase = create_client(url, key)
genai.configure(api_key=gemini_key)

# Use gemini-1.5-pro with 2M context
model = genai.GenerativeModel('gemini-1.5-pro')

print('Pure Tweet Analysis with Gemini 1.5 Pro')
print('=' * 80)

# Get ALL tweets - no filtering, no preprocessing
print('Loading all tweets...')
all_tweets = []
offset = 0

while True:
    result = supabase.table('crypto_calls') \
        .select('ticker, x_raw_tweets, created_at') \
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
        
        ticker = call.get('ticker', 'Unknown')
        date = call.get('created_at', '')[:10]
        
        # Extract all tweets
        for tweet in x_tweets:
            if isinstance(tweet, dict):
                text = tweet.get('text', '')
                if text and len(text) > 20:
                    all_tweets.append(f"{ticker} ({date}): {text}")
    
    offset += len(result.data)
    print(f'Processed {offset} calls...')

print(f'\nTotal tweets collected: {len(all_tweets):,}')

# Build simple prompt
prompt = """I have a large collection of tweets about cryptocurrency projects. Your task is to identify the 50 tweets that show the HIGHEST legitimacy factors.

KEETA is the gold standard example: A cross-border payments fintech with $17M funding from Eric Schmidt (ex-Google CEO), featured in TechCrunch, with named founder Ty Schenk.

Look for tweets mentioning:
- Real funding amounts with named investors
- Real companies and verifiable partnerships
- Named founders with backgrounds
- Press coverage from major outlets
- Live products with user metrics
- Regulatory compliance or licenses

IGNORE:
- Price predictions
- Chart analysis
- Vague claims
- Hype and speculation

Here are all the tweets:

"""

# Add all tweets
for tweet in all_tweets:
    prompt += tweet + "\n"

prompt += """

From ALL the tweets above, identify the TOP 50 with the highest legitimacy indicators. Return them in this format:

RANK. TICKER (DATE): [Full tweet text]
LEGITIMACY FACTORS: [Specific factors that make this legitimate]

Be extremely selective. Most crypto tweets are hype. Focus only on concrete, verifiable claims."""

# Check size
prompt_chars = len(prompt)
estimated_tokens = prompt_chars // 4

print(f'\nPrompt size: {prompt_chars:,} characters (~{estimated_tokens:,} tokens)')
print(f'Using {estimated_tokens/2_097_152*100:.1f}% of 2M token limit')

print('\nSending ALL tweets to Gemini for analysis...')
print('Looking for the 50 most legitimate tweets from the entire dataset...\n')

try:
    response = model.generate_content(
        prompt,
        generation_config=genai.types.GenerationConfig(
            temperature=0,
            max_output_tokens=8192,
        )
    )
    
    print('='*80)
    print('TOP 50 MOST LEGITIMATE TWEETS FOUND:')
    print('='*80)
    print(response.text)
    
    # Save results
    with open('top_50_legitimate_tweets.txt', 'w') as f:
        f.write('TOP 50 MOST LEGITIMATE CRYPTO TWEETS\n')
        f.write('='*80 + '\n')
        f.write(f'Analyzed {len(all_tweets):,} total tweets\n')
        f.write('='*80 + '\n\n')
        f.write(response.text)
    
    print(f'\nResults saved to: top_50_legitimate_tweets.txt')
    
except Exception as e:
    print(f'\nError: {e}')
    print('\nYour API key appears to be on the free tier.')
    print('To process this much data, you need:')
    print('1. A Google Cloud project with billing enabled')
    print('2. The Gemini API enabled on that project')
    print('3. An API key from that project (not the free AI Studio key)')