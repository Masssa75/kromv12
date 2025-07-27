#!/usr/bin/env python3
"""Find calls with high-profile endorsements or backing"""

import os
import json
import re
from supabase import create_client, Client
from dotenv import load_dotenv
from collections import defaultdict

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

supabase: Client = create_client(url, key)

print("Scanning for high-profile crypto calls...")
print("=" * 60)

# Define patterns to search for
high_profile_patterns = {
    'tech_leaders': [
        'eric schmidt', 'elon', 'musk', 'vitalik', 'buterin', 'cz_binance', 'cz ',
        'brian armstrong', 'sam altman', 'jack dorsey', 'mark cuban', 'michael saylor',
        'cathie wood', 'raoul pal', 'arthur hayes', 'su zhu', 'kyle davies',
        'do kwon', 'andre cronje', 'hayden adams', 'sergey nazarov', 'gavin wood',
        'charles hoskinson', 'anatoly yakovenko', 'raj gokal', 'kris marszalek',
        'jesse powell', 'winklevoss', 'barry silbert', 'mike novogratz',
        'dan morehead', 'matt huang', 'fred ehrsam', 'balaji', 'naval'
    ],
    'investment_terms': [
        'lead investor', 'backed by', 'investment from', 'funding round', 
        'million funding', 'million round', 'series a', 'series b', 'seed round',
        'invested in', 'investor', 'vc backed', 'venture capital', 'portfolio company',
        'incubated by', 'accelerator', 'y combinator', 'yc', 'techstars'
    ],
    'major_companies': [
        'google', 'microsoft', 'meta', 'facebook', 'amazon', 'apple', 'tesla',
        'coinbase', 'binance', 'ftx', 'kraken', 'crypto.com', 'opensea',
        'uniswap', 'aave', 'compound', 'makerdao', 'chainlink', 'polygon',
        'avalanche', 'solana labs', 'ethereum foundation', 'consensys',
        'a16z', 'paradigm', 'sequoia', 'pantera', 'galaxy digital',
        'grayscale', 'microstrategy', 'paypal', 'square', 'block'
    ],
    'endorsement_terms': [
        'liked', 'tweeted', 'retweeted', 'replied', 'followed', 'endorsed',
        'backed', 'supports', 'advisor', 'team includes', 'founded by',
        'created by', 'developed by', 'partnership with', 'collaboration'
    ]
}

# Flatten all patterns for easier searching
all_patterns = []
for category, patterns in high_profile_patterns.items():
    all_patterns.extend(patterns)

# Results storage
high_profile_calls = defaultdict(list)
pattern_matches = defaultdict(int)

# Fetch all calls with pagination
offset = 0
page_size = 1000
total_processed = 0

try:
    while True:
        print(f"\nFetching rows {offset} to {offset + page_size}...")
        
        result = supabase.table('crypto_calls') \
            .select('ticker, raw_data, analysis_tier, x_analysis_tier, created_at') \
            .order('created_at', desc=True) \
            .range(offset, offset + page_size - 1) \
            .execute()
        
        if not result.data:
            break
        
        # Process each call
        for call in result.data:
            raw_data = call.get('raw_data')
            if not raw_data:
                continue
                
            if isinstance(raw_data, str):
                try:
                    raw_data = json.loads(raw_data)
                except:
                    continue
            
            if isinstance(raw_data, dict):
                message = raw_data.get('text', '').lower()
                
                # Check for high-profile patterns
                matched_patterns = []
                for pattern in all_patterns:
                    if pattern in message:
                        matched_patterns.append(pattern)
                        pattern_matches[pattern] += 1
                
                if matched_patterns:
                    # Categorize the matches
                    categories = []
                    for category, patterns in high_profile_patterns.items():
                        if any(p in matched_patterns for p in patterns):
                            categories.append(category)
                    
                    high_profile_calls[call['ticker']].append({
                        'ticker': call['ticker'],
                        'created_at': call['created_at'],
                        'claude_tier': call.get('analysis_tier', 'N/A'),
                        'x_tier': call.get('x_analysis_tier', 'N/A'),
                        'matched_patterns': matched_patterns,
                        'categories': categories,
                        'message_preview': raw_data.get('text', '')[:200] + '...'
                    })
        
        total_processed += len(result.data)
        print(f"Processed {total_processed} calls, found {len(high_profile_calls)} potential high-profile tokens")
        
        if len(result.data) < page_size:
            break
            
        offset += page_size
    
    # Display results
    print("\n" + "=" * 60)
    print("HIGH-PROFILE CALLS FOUND")
    print("=" * 60)
    
    # Sort by number of mentions
    sorted_tokens = sorted(high_profile_calls.items(), key=lambda x: len(x[1]), reverse=True)
    
    print(f"\nTotal unique tokens with high-profile mentions: {len(sorted_tokens)}")
    print("\nTop 20 tokens by mention frequency:")
    
    for ticker, calls in sorted_tokens[:20]:
        print(f"\n{ticker} - {len(calls)} mentions")
        # Show the first call for this token
        first_call = calls[0]
        print(f"  First mention: {first_call['created_at']}")
        print(f"  Ratings: Claude={first_call['claude_tier']}, X={first_call['x_tier']}")
        print(f"  Matched: {', '.join(first_call['matched_patterns'][:3])}")
        print(f"  Message: {first_call['message_preview']}")
    
    # Show most common patterns
    print("\n" + "=" * 60)
    print("MOST COMMON HIGH-PROFILE PATTERNS")
    print("=" * 60)
    
    sorted_patterns = sorted(pattern_matches.items(), key=lambda x: x[1], reverse=True)
    for pattern, count in sorted_patterns[:15]:
        print(f"{pattern}: {count} mentions")
    
    # Find tokens that were rated low despite high-profile backing
    print("\n" + "=" * 60)
    print("POTENTIALLY UNDERRATED CALLS (High-profile but rated BASIC/TRASH)")
    print("=" * 60)
    
    underrated = []
    for ticker, calls in high_profile_calls.items():
        for call in calls:
            if (call['claude_tier'] in ['BASIC', 'TRASH'] and 
                call['x_tier'] in ['BASIC', 'TRASH'] and
                len(call['matched_patterns']) >= 2):  # At least 2 high-profile mentions
                underrated.append(call)
    
    # Show top 10 potentially underrated
    underrated_sorted = sorted(underrated, key=lambda x: len(x['matched_patterns']), reverse=True)
    for call in underrated_sorted[:10]:
        print(f"\n{call['ticker']} - {call['created_at']}")
        print(f"  Ratings: Claude={call['claude_tier']}, X={call['x_tier']}")
        print(f"  High-profile mentions: {', '.join(call['matched_patterns'])}")
        print(f"  Message: {call['message_preview']}")
    
    # Save detailed results
    with open('high_profile_calls_analysis.json', 'w') as f:
        json.dump({
            'total_processed': total_processed,
            'tokens_found': len(high_profile_calls),
            'pattern_matches': dict(pattern_matches),
            'top_tokens': [(ticker, len(calls)) for ticker, calls in sorted_tokens[:50]]
        }, f, indent=2)
    
    print(f"\nDetailed results saved to high_profile_calls_analysis.json")
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()