#!/usr/bin/env python3

import os
import json
from supabase import create_client, Client

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase: Client = create_client(url, key)

print("🔍 Checking X analysis model data...")

# Get calls with X analysis scores and their model info
response = supabase.table('crypto_calls').select(
    'krom_id, ticker, x_analysis_score, x_analysis_model, analysis_model, created_at'
).not_('x_analysis_score', 'is', 'null').order('created_at', desc=True).limit(10).execute()

calls = response.data

print(f"📊 Found {len(calls)} calls with X analysis scores\n")

for call in calls:
    print(f"Token: {call['ticker']}")
    print(f"  X Analysis Score: {call['x_analysis_score']}")
    print(f"  X Analysis Model: {call['x_analysis_model']}")  
    print(f"  Call Analysis Model: {call['analysis_model']}")
    print(f"  Created: {call['created_at']}")
    print()

# Check specific token from screenshot (INUMINATI)  
print("🎯 Checking INUMINATI specifically...")
inuminati = supabase.table('crypto_calls').select(
    'krom_id, ticker, x_analysis_score, x_analysis_model, analysis_model, x_analysis_reasoning'
).eq('ticker', 'INUMINATI').execute()

if inuminati.data:
    token = inuminati.data[0]
    print(f"INUMINATI data:")
    print(f"  Krom ID: {token.get('krom_id')}")
    print(f"  X Analysis Score: {token.get('x_analysis_score')}")
    print(f"  X Analysis Model: {token.get('x_analysis_model')}")
    print(f"  X Analysis Reasoning: {token.get('x_analysis_reasoning', 'None')[:100] if token.get('x_analysis_reasoning') else 'None'}...")
    print(f"  Call Analysis Model: {token.get('analysis_model')}")
else:
    print("❌ INUMINATI not found")

# Check if any records have x_analysis_model populated
print("\n🔍 Checking x_analysis_model field status...")
try:
    # Get all calls with X analysis scores  
    all_x_calls = supabase.table('crypto_calls').select(
        'ticker, x_analysis_score, x_analysis_model'
    ).not_('x_analysis_score', 'is', 'null').limit(20).execute()
    
    print(f"Found {len(all_x_calls.data)} calls with X analysis scores")
    
    with_model = 0
    without_model = 0
    
    for call in all_x_calls.data:
        if call['x_analysis_model']:
            with_model += 1
        else:
            without_model += 1
    
    print(f"  With x_analysis_model: {with_model}")
    print(f"  Without x_analysis_model: {without_model}")
    
    # Show some examples
    if with_model > 0:
        model_examples = [call for call in all_x_calls.data if call['x_analysis_model']][:3]
        print("\n📋 Examples with models:")
        for call in model_examples:
            print(f"  {call['ticker']}: {call['x_analysis_model']}")
            
    if without_model > 0:
        no_model_examples = [call for call in all_x_calls.data if not call['x_analysis_model']][:3]
        print("\n❌ Examples without models:")
        for call in no_model_examples:
            print(f"  {call['ticker']}: x_analysis_model = {call['x_analysis_model']}")
            
except Exception as e:
    print(f"Error checking models: {e}")