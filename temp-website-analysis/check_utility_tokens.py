#!/usr/bin/env python3
"""Check utility tokens in Supabase"""
import requests

# Supabase credentials
url = 'https://eucfoommxxvqmmwdbkdv.supabase.co'
service_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Ria2R2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzU2Mjg4MSwiZXhwIjoyMDYzMTM4ODgxfQ.VcC7Bp3zMFYor3eVDonoG7BuS7AavemQnSOhrWcY5Y4'

headers = {
    'apikey': service_key,
    'Authorization': f'Bearer {service_key}'
}

# Get tokens where either analysis says 'utility'
response = requests.get(
    f'{url}/rest/v1/crypto_calls',
    headers=headers,
    params={
        'select': 'ticker,website_url,analysis_token_type,x_analysis_token_type,liquidity_usd',
        'is_invalidated': 'eq.false',
        'or': '(analysis_token_type.eq.utility,x_analysis_token_type.eq.utility)',
        'website_url': 'not.is.null',
        'order': 'liquidity_usd.desc.nullsfirst',
        'limit': '1000'
    }
)

if response.status_code == 200:
    tokens = response.json()
    
    # Get unique websites
    unique_websites = set()
    tokens_with_websites = []
    
    # Count by classification
    both_utility = 0
    only_call_utility = 0
    only_x_utility = 0
    
    for token in tokens:
        if token.get('website_url'):
            website = token['website_url']
            
            # Count classification agreements
            call_type = (token.get('analysis_token_type') or '').lower()
            x_type = (token.get('x_analysis_token_type') or '').lower()
            
            if call_type == 'utility' and x_type == 'utility':
                both_utility += 1
            elif call_type == 'utility':
                only_call_utility += 1
            elif x_type == 'utility':
                only_x_utility += 1
                
            if website not in unique_websites:
                unique_websites.add(website)
                tokens_with_websites.append(token)
    
    print(f'📊 UTILITY Tokens in Supabase (non-dead with websites):')
    print(f'='*60)
    print(f'Total utility tokens: {len(tokens)}')
    print(f'Unique websites: {len(unique_websites)}')
    print(f'')
    print(f'Classification breakdown:')
    print(f'  Both AIs say utility: {both_utility}')
    print(f'  Only call analysis says utility: {only_call_utility}')
    print(f'  Only X analysis says utility: {only_x_utility}')
    
    print(f'\nFirst 15 utility tokens:')
    for i, token in enumerate(tokens_with_websites[:15], 1):
        call_type = token.get('analysis_token_type', 'N/A')
        x_type = token.get('x_analysis_token_type', 'N/A')
        liq = token.get('liquidity_usd', 0) or 0
        print(f'  {i}. {token["ticker"]}: [Call: {call_type}, X: {x_type}] Liq: ${int(liq):,}')
        print(f'     {token["website_url"][:50]}...')
        
    print(f'\n💡 Summary:')
    print(f'  - Local SQLite has: 128 tokens')
    print(f'  - Supabase has: {len(unique_websites)} unique utility token websites')
    print(f'  - Need to analyze: {len(unique_websites) - 4} more (4 already done)')
else:
    print(f'Error: {response.status_code}')
    print(response.text)