#!/usr/bin/env python3
"""
Update website_analysis database with contract addresses from Supabase
"""
import requests
import sqlite3
from urllib.parse import urlparse

def normalize_url(url):
    """Normalize URL for comparison"""
    # Remove protocol variations
    url = url.replace('https://www.', 'https://').replace('http://www.', 'http://').replace('http://', 'https://')
    # Remove trailing slash
    if url.endswith('/'):
        url = url[:-1]
    return url.lower()

def get_tokens_from_supabase():
    """Fetch all tokens with websites and contract addresses from Supabase"""
    url = 'https://eucfoommxxvqmmwdbkdv.supabase.co'
    service_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Ria2R2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzU2Mjg4MSwiZXhwIjoyMDYzMTM4ODgxfQ.VcC7Bp3zMFYor3eVDonoG7BuS7AavemQnSOhrWcY5Y4'
    
    headers = {
        'apikey': service_key,
        'Authorization': f'Bearer {service_key}'
    }
    
    print("Fetching tokens from Supabase...")
    response = requests.get(
        f'{url}/rest/v1/crypto_calls',
        headers=headers,
        params={
            'select': 'ticker,website_url,contract_address,network',
            'website_url': 'not.is.null',
            'contract_address': 'not.is.null',
            'limit': '10000'
        },
        timeout=30
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Error fetching from Supabase: {response.status_code}')
        return []

def main():
    print("\n" + "="*80)
    print("CONTRACT ADDRESS UPDATE SCRIPT")
    print("="*80)
    
    # Get tokens from Supabase
    tokens = get_tokens_from_supabase()
    print(f"✅ Found {len(tokens)} tokens with websites and contract addresses")
    
    # Create mapping from normalized URL to contract info
    url_to_contract = {}
    for token in tokens:
        url = normalize_url(token['website_url'])
        # Store first match or prefer non-pump.fun contracts
        if url not in url_to_contract or 'pump' not in token.get('contract_address', ''):
            url_to_contract[url] = {
                'contract': token['contract_address'],
                'ticker': token['ticker'],
                'network': token.get('network', 'Unknown')
            }
    
    print(f"📊 Unique websites with contracts: {len(url_to_contract)}")
    
    # Connect to local database
    conn = sqlite3.connect('website_analysis_new.db')
    cursor = conn.cursor()
    
    # Get all analyzed websites
    cursor.execute("SELECT id, url, ticker FROM website_analysis")
    rows = cursor.fetchall()
    
    print(f"\n🔍 Checking {len(rows)} analyzed websites...")
    
    updated = 0
    matched = 0
    
    for row_id, url, ticker in rows:
        normalized = normalize_url(url)
        
        if normalized in url_to_contract:
            contract_info = url_to_contract[normalized]
            cursor.execute(
                "UPDATE website_analysis SET contract_address = ? WHERE id = ?",
                (contract_info['contract'], row_id)
            )
            updated += 1
            matched += 1
            print(f"  ✅ {ticker}: {contract_info['contract'][:20]}... ({contract_info['network']})")
        else:
            # Try without www
            alt_url = normalized.replace('https://', 'https://www.')
            if alt_url in url_to_contract:
                contract_info = url_to_contract[alt_url]
                cursor.execute(
                    "UPDATE website_analysis SET contract_address = ? WHERE id = ?",
                    (contract_info['contract'], row_id)
                )
                updated += 1
                matched += 1
                print(f"  ✅ {ticker}: {contract_info['contract'][:20]}... (alt match)")
    
    conn.commit()
    conn.close()
    
    print(f"\n📈 Summary:")
    print(f"  - Total websites analyzed: {len(rows)}")
    print(f"  - Contract addresses found: {matched}")
    print(f"  - Database records updated: {updated}")
    print(f"  - Coverage: {matched/len(rows)*100:.1f}%")
    
    print("\n✨ Contract addresses updated successfully!")

if __name__ == '__main__':
    main()