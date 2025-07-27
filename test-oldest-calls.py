#!/usr/bin/env python3
"""
Test fetching and analyzing oldest calls
"""

import os
from datetime import datetime
from supabase import create_client
from anthropic import Anthropic
from dotenv import load_dotenv
import json

load_dotenv()

# Initialize clients
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

anthropic = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

print("=== Testing Oldest Calls Analysis ===\n")

# Step 1: Fetch 5 oldest calls
print("1. Fetching 5 oldest calls from Supabase...")
try:
    result = supabase.table('crypto_calls') \
        .select('krom_id, ticker, buy_timestamp, raw_data') \
        .not_.is_('raw_data', 'null') \
        .order('buy_timestamp', desc=False) \
        .limit(5) \
        .execute()
    
    if result.data:
        print(f"✓ Found {len(result.data)} oldest calls\n")
        
        for i, call in enumerate(result.data, 1):
            print(f"Call {i}:")
            print(f"  Token: {call.get('ticker', 'Unknown')}")
            print(f"  Date: {call.get('buy_timestamp', 'Unknown')}")
            print(f"  ID: {call.get('krom_id', '')[:8]}...")
            
            raw_data = call.get('raw_data', {})
            if raw_data:
                print(f"  Group: {raw_data.get('group', {}).get('name', 'Unknown')}")
                print(f"  Message preview: {raw_data.get('text', '')[:50]}...")
            print()
    else:
        print("✗ No calls found")
        
except Exception as e:
    print(f"✗ Error fetching calls: {e}")

# Step 2: Analyze first call as example
if result.data:
    print("\n2. Analyzing first call as example...")
    first_call = result.data[0]
    
    raw_data = first_call.get('raw_data', {})
    ticker = first_call.get('ticker', 'Unknown')
    message = raw_data.get('text', 'No message')[:500]  # Limit message length
    group = raw_data.get('group', {}).get('name', 'Unknown')
    
    prompt = f"""Analyze this crypto call for legitimacy.

Token: {ticker}
Group: {group}
Message: {message}

Score 1-10 (1-3: shitcoin, 4-7: some legitimacy, 8-10: major backing)

Respond with JSON only:
{{
  "score": <number>,
  "legitimacy_factor": "<1-6 words>",
  "explanation": "<brief>"
}}"""

    try:
        print(f"Analyzing {ticker} with Claude Haiku...")
        
        response = anthropic.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=300,
            temperature=0.3,
            messages=[{"role": "user", "content": prompt}]
        )
        
        result_text = response.content[0].text
        print(f"\nRaw response: {result_text}\n")
        
        # Parse JSON
        start = result_text.find('{')
        end = result_text.rfind('}') + 1
        if start >= 0 and end > start:
            result = json.loads(result_text[start:end])
            print(f"✓ Analysis complete:")
            print(f"  Score: {result.get('score', 'N/A')}/10")
            print(f"  Legitimacy: {result.get('legitimacy_factor', 'N/A')}")
            print(f"  Explanation: {result.get('explanation', 'N/A')}")
        
    except Exception as e:
        print(f"✗ Analysis error: {e}")

print("\n✓ Test complete!")