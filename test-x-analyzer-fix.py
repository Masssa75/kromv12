#!/usr/bin/env python3
"""
Test the improved X analyzer logic manually
"""
import os
import requests
import json
import re
from dotenv import load_dotenv

load_dotenv()

def test_improved_analyzer():
    scraperapi_key = os.getenv('SCRAPERAPI_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')
    
    if not scraperapi_key or not anthropic_key:
        print("Error: Missing API keys")
        return
    
    contract_address = "DrZ26cKJDksVRWib3DVVsjo9eeXccc7hKhDJviiYEEZY"
    
    print(f"Testing improved X analyzer for contract: {contract_address}")
    
    # Test new search with f=top
    target_url = f"https://nitter.net/search?q={contract_address}&f=top"
    scraper_url = f"https://api.scraperapi.com/?api_key={scraperapi_key}&url={requests.utils.quote(target_url)}"
    
    print(f"Fetching: {target_url}")
    
    response = requests.get(scraper_url)
    if not response.ok:
        print(f"ScraperAPI error: {response.status_code}")
        return
    
    html = response.text
    print(f"Received HTML response, length: {len(html)}")
    
    # Extract tweets with improved parsing
    tweet_pattern = r'<div class="tweet-content[^"]*"[^>]*>(.*?)</div>'
    tweet_matches = re.finditer(tweet_pattern, html, re.DOTALL | re.IGNORECASE)
    
    tweets = []
    for match in tweet_matches:
        content = match.group(1)
        # Preserve links and mentions before removing HTML
        content = re.sub(r'<a[^>]*href="[^"]*"[^>]*>(.*?)</a>', r'\1', content, flags=re.IGNORECASE)
        content = re.sub(r'<[^>]*>', ' ', content)  # Remove remaining HTML tags
        content = re.sub(r'\s+', ' ', content)  # Normalize whitespace
        content = content.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>').replace('&quot;', '"')
        content = content.strip()
        
        # Quality filtering: prioritize substantial tweets with good content
        if content and len(content) > 30 and not re.match(r'^[a-zA-Z0-9]{40,}$', content):
            tweets.append({
                'text': content,
                'length': len(content)
            })
        
        if len(tweets) >= 15:
            break
    
    # Sort by length to prioritize more substantial tweets
    tweets.sort(key=lambda x: x['length'], reverse=True)
    
    print(f"Found {len(tweets)} quality tweets")
    
    # Show top 5 tweets
    print("\nTop 5 tweets by length:")
    for i, tweet in enumerate(tweets[:5]):
        print(f"{i+1}. ({tweet['length']} chars) {tweet['text'][:100]}...")
    
    if not tweets:
        print("No tweets found!")
        return
    
    # Prepare for Claude analysis
    top_tweets = tweets[:10]
    tweet_content = '\n\n'.join([f"Tweet {i+1}: {tweet['text']}" for i, tweet in enumerate(top_tweets)])
    
    print(f"\nAnalyzing {len(top_tweets)} tweets with Claude...")
    
    # Claude analysis
    claude_response = requests.post('https://api.anthropic.com/v1/messages', 
        headers={
            'Content-Type': 'application/json',
            'x-api-key': anthropic_key,
            'anthropic-version': '2023-06-01'
        },
        json={
            'model': 'claude-3-haiku-20240307',
            'max_tokens': 500,
            'temperature': 0,
            'system': """Analyze these crypto tweets and provide ULTRA-CONCISE insights.

TIER: Choose ONE: ALPHA, SOLID, BASIC, or TRASH

SUMMARY: Maximum 3 bullet points, 10 words each:
• Project purpose (if found)
• Team/backers (if notable)  
• Key detail (if any)

RED FLAGS: Maximum 2 points, 5 words each:
• Main concern
• Secondary risk

Keep it EXTREMELY brief. No fluff. Facts only.""",
            'messages': [{
                'role': 'user',
                'content': f'Analyze these tweets about contract address {contract_address}:\n\n{tweet_content}'
            }]
        }
    )
    
    if not claude_response.ok:
        print(f"Claude API error: {claude_response.status_code}")
        print(claude_response.text)
        return
    
    result = claude_response.json()
    analysis = result['content'][0]['text']
    
    print(f"\n=== CLAUDE ANALYSIS ===")
    print(analysis)
    
    # Parse results
    tier_match = re.search(r'TIER:\s*(\w+)', analysis, re.IGNORECASE)
    tier = tier_match.group(1).upper() if tier_match else 'TRASH'
    
    print(f"\n=== FINAL RESULT ===")
    print(f"TIER: {tier}")
    print(f"Tweets analyzed: {len(top_tweets)}")
    print(f"Quality improvement: Using f=top instead of f=tweets, better parsing, length-based filtering")

if __name__ == "__main__":
    test_improved_analyzer()