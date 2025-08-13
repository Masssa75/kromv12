#!/usr/bin/env python3
"""
Analyze a single specific token
"""

import os
import sys
sys.path.append('..')
from dotenv import load_dotenv
import requests

# Load environment variables  
load_dotenv('../.env')

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

# Import analyzer
from website_analyzer import WebsiteAnalyzer

def analyze_sui_token():
    headers = {
        'apikey': SUPABASE_SERVICE_ROLE_KEY,
        'Authorization': f'Bearer {SUPABASE_SERVICE_ROLE_KEY}',
        'Content-Type': 'application/json'
    }
    
    # Query for SUI token specifically
    query = '''
        select=id,ticker,network,website_url,analysis_score,x_analysis_score,contract_address
        &ticker=eq.SUI
        &network=eq.ethereum
        &website_url=eq.https://suioneth.com/
        &limit=1
    '''.replace('\n', '').replace('    ', '')
    
    url = f"{SUPABASE_URL}/rest/v1/crypto_calls?{query}"
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200 and response.json():
        token = response.json()[0]
        print(f"Analyzing {token['ticker']} - {token['website_url']}")
        
        analyzer = WebsiteAnalyzer()
        analysis = analyzer.analyze_website(token)
        
        if analysis:
            analyzer.save_analysis(token, analysis)
            print(f"✓ Score: {analysis.get('website_score')}/10")
            print(f"✓ Tier: {analysis.get('website_tier')}")
            if analysis.get('website_summary'):
                print(f"✓ Summary: {analysis['website_summary'][:200]}...")
        else:
            print("Analysis failed")
    else:
        print("Could not find SUI token")

if __name__ == "__main__":
    analyze_sui_token()