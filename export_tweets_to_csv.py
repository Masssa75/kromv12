#!/usr/bin/env python3
"""
Export all tweets from Supabase crypto_calls table to CSV
"""

import os
import csv
import json
from datetime import datetime
from supabase import create_client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    # Initialize Supabase client
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    
    if not url or not key:
        print("Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env file")
        return
    
    print(f"Connecting to Supabase: {url}")
    supabase = create_client(url, key)
    
    # Query all records with tweet data
    print("Fetching all records with tweet data...")
    all_records = []
    limit = 1000
    offset = 0
    
    while True:
        try:
            result = supabase.table('crypto_calls') \
                .select('krom_id, ticker, buy_timestamp, x_raw_tweets, x_analysis_tier, x_analysis_summary, x_analyzed_at') \
                .not_.is_('x_raw_tweets', 'null') \
                .range(offset, offset + limit - 1) \
                .execute()
            
            if not result.data:
                break
                
            all_records.extend(result.data)
            print(f"Fetched {len(result.data)} records (total: {len(all_records)})")
            
            if len(result.data) < limit:
                break
                
            offset += limit
            
        except Exception as e:
            print(f"Error fetching data: {e}")
            break
    
    print(f"\nTotal records with tweets: {len(all_records)}")
    
    # Prepare CSV data
    csv_rows = []
    
    for record in all_records:
        krom_id = record.get('krom_id', '')
        ticker = record.get('ticker', '')
        buy_timestamp = record.get('buy_timestamp', '')
        x_analysis_tier = record.get('x_analysis_tier', '')
        x_analysis_summary = record.get('x_analysis_summary', '')
        x_analyzed_at = record.get('x_analyzed_at', '')
        
        # Convert timestamps to readable format
        if buy_timestamp:
            try:
                buy_date = datetime.fromisoformat(buy_timestamp.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
            except:
                buy_date = buy_timestamp
        else:
            buy_date = ''
            
        if x_analyzed_at:
            try:
                analyzed_date = datetime.fromisoformat(x_analyzed_at.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
            except:
                analyzed_date = x_analyzed_at
        else:
            analyzed_date = ''
        
        # Extract tweets
        x_raw_tweets = record.get('x_raw_tweets', [])
        if isinstance(x_raw_tweets, str):
            try:
                x_raw_tweets = json.loads(x_raw_tweets)
            except:
                x_raw_tweets = []
        
        # Create a row for each tweet
        if x_raw_tweets and isinstance(x_raw_tweets, list):
            for i, tweet in enumerate(x_raw_tweets, 1):
                tweet_text = tweet.get('text', '') if isinstance(tweet, dict) else str(tweet)
                csv_rows.append({
                    'krom_id': krom_id,
                    'ticker': ticker,
                    'buy_date': buy_date,
                    'tweet_number': i,
                    'tweet_text': tweet_text,
                    'analysis_tier': x_analysis_tier,
                    'analysis_summary': x_analysis_summary,
                    'analyzed_date': analyzed_date
                })
        else:
            # No tweets found, still create a row to show the record
            csv_rows.append({
                'krom_id': krom_id,
                'ticker': ticker,
                'buy_date': buy_date,
                'tweet_number': 0,
                'tweet_text': 'No tweets found',
                'analysis_tier': x_analysis_tier,
                'analysis_summary': x_analysis_summary,
                'analyzed_date': analyzed_date
            })
    
    # Write to CSV
    csv_filename = f'kromv12_tweets_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['krom_id', 'ticker', 'buy_date', 'tweet_number', 'tweet_text', 
                     'analysis_tier', 'analysis_summary', 'analyzed_date']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(csv_rows)
    
    print(f"\nExported {len(csv_rows)} tweet rows to {csv_filename}")
    
    # Print summary statistics
    unique_tickers = len(set(row['ticker'] for row in csv_rows))
    tier_counts = {}
    for row in csv_rows:
        tier = row['analysis_tier']
        if tier:
            tier_counts[tier] = tier_counts.get(tier, 0) + 1
    
    print(f"\nSummary:")
    print(f"- Total unique tickers: {unique_tickers}")
    print(f"- Total tweet entries: {len(csv_rows)}")
    print(f"- Analysis tier breakdown:")
    for tier, count in sorted(tier_counts.items()):
        print(f"  - {tier}: {count}")

if __name__ == "__main__":
    main()