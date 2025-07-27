#!/usr/bin/env python3
"""Scan all tweets for legitimate statements and rank them"""

import json
import re
from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv()
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
supabase = create_client(url, key)

print('Scanning all X/Twitter data for legitimate statements...')
print('=' * 80)

# Patterns for legitimate indicators
legitimacy_patterns = {
    'funding': r'(\$\d+[MK]?\s*(funding|raised|round|Series [A-Z])|Series [A-Z]\s*(round|funding)?|\d+\s*million\s*(dollar|usd|funding|raised)|seed\s*(round|funding|investment)|pre-?seed)',
    'company': r'(Google|Microsoft|Amazon|Meta|Apple|Tesla|Coinbase|Binance|Sequoia|a16z|Paradigm|Fortune\s*500|Forbes|TechCrunch|Bloomberg|Y\s*Combinator|YC)',
    'team': r'(founder|co-?founder|CEO|CTO|CFO|CMO|ex-?(Google|Facebook|Amazon|Microsoft|Apple|Coinbase|Meta|Twitter|Uber|Goldman|JPMorgan))',
    'metrics': r'(\d+[MK]?\s*(users|downloads|customers|transactions|revenue)|DAU|MAU|ARR|MRR)',
    'partnerships': r'(partnership|partnered|collaboration|integration|backed by|supported by|invested by)',
    'product': r'(launched|launching|live on|available on|app store|google play|mainnet|testnet)'
}

# Get all calls with X data
print('Fetching all calls with X analysis...')
offset = 0
legitimate_tweets = []

while True:
    result = supabase.table('crypto_calls') \
        .select('ticker, x_raw_tweets, created_at, krom_id') \
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
        
        for tweet in x_tweets:
            tweet_text = tweet.get('text', '') if isinstance(tweet, dict) else str(tweet)
            if len(tweet_text) < 20:  # Skip very short tweets
                continue
            
            # Check for legitimate indicators
            found_patterns = []
            legitimacy_score = 0
            
            for pattern_type, pattern in legitimacy_patterns.items():
                matches = re.findall(pattern, tweet_text, re.IGNORECASE)
                if matches:
                    found_patterns.append((pattern_type, matches))
                    # Scoring based on pattern type
                    if pattern_type == 'funding':
                        legitimacy_score += 5
                    elif pattern_type == 'company':
                        legitimacy_score += 4
                    elif pattern_type == 'team':
                        legitimacy_score += 3
                    elif pattern_type == 'metrics':
                        legitimacy_score += 3
                    elif pattern_type == 'partnerships':
                        legitimacy_score += 2
                    elif pattern_type == 'product':
                        legitimacy_score += 1
            
            if found_patterns and legitimacy_score >= 3:  # Only keep substantial mentions
                legitimate_tweets.append({
                    'ticker': ticker,
                    'score': legitimacy_score,
                    'tweet': tweet_text[:500],  # Truncate long tweets
                    'patterns': found_patterns,
                    'date': call.get('created_at', '')[:10]
                })
    
    offset += len(result.data)
    if offset >= 4560:  # We know there are ~4560 calls
        break

print(f'\nFound {len(legitimate_tweets)} tweets with legitimate indicators')

# Sort by score
legitimate_tweets.sort(key=lambda x: x['score'], reverse=True)

# Save to file for analysis
with open('/tmp/legitimate_tweets.txt', 'w') as f:
    f.write('MOST LEGITIMATE STATEMENTS FROM X/TWITTER DATA\n')
    f.write('=' * 80 + '\n\n')
    
    current_score = None
    rank = 1
    
    for tweet_data in legitimate_tweets[:100]:  # Top 100
        if tweet_data['score'] != current_score:
            current_score = tweet_data['score']
            f.write(f'\n--- LEGITIMACY SCORE: {current_score} ---\n\n')
        
        f.write(f'{rank}. {tweet_data["ticker"]} ({tweet_data["date"]})\n')
        f.write(f'   Patterns found: ')
        for pattern_type, matches in tweet_data['patterns']:
            f.write(f'{pattern_type}: {matches[0]}, ')
        f.write(f'\n   Tweet: {tweet_data["tweet"]}\n\n')
        rank += 1

print(f'\nTop 10 most legitimate statements:\n')
for i, tweet_data in enumerate(legitimate_tweets[:10]):
    print(f'{i+1}. {tweet_data["ticker"]} (Score: {tweet_data["score"]})')
    print(f'   Found: ', end='')
    for pattern_type, matches in tweet_data['patterns']:
        print(f'{pattern_type}={matches[0]}, ', end='')
    print(f'\n   Tweet: {tweet_data["tweet"][:200]}...')
    print()

print(f'\nFull results saved to /tmp/legitimate_tweets.txt')