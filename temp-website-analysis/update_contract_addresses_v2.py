#!/usr/bin/env python3
"""
Update website_analysis database with contract addresses from Supabase
Version 2: Match by ticker symbol instead of URL
"""
import requests
import sqlite3

def get_all_tokens_from_supabase():
    """Fetch ALL tokens with contract addresses from Supabase"""
    url = 'https://eucfoommxxvqmmwdbkdv.supabase.co'
    service_key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImV1Y2Zvb21teHh2cW1td2Ria2R2Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NzU2Mjg4MSwiZXhwIjoyMDYzMTM4ODgxfQ.VcC7Bp3zMFYor3eVDonoG7BuS7AavemQnSOhrWcY5Y4'
    
    headers = {
        'apikey': service_key,
        'Authorization': f'Bearer {service_key}'
    }
    
    print("Fetching ALL tokens from Supabase...")
    all_tokens = []
    offset = 0
    limit = 1000
    
    while True:
        response = requests.get(
            f'{url}/rest/v1/crypto_calls',
            headers=headers,
            params={
                'select': 'ticker,contract_address,network',
                'contract_address': 'not.is.null',
                'limit': limit,
                'offset': offset
            },
            timeout=30
        )
        
        if response.status_code == 200:
            batch = response.json()
            if not batch:
                break
            all_tokens.extend(batch)
            print(f"  Fetched {len(all_tokens)} tokens so far...")
            if len(batch) < limit:
                break
            offset += limit
        else:
            print(f'Error fetching from Supabase: {response.status_code}')
            break
    
    return all_tokens

def main():
    print("\n" + "="*80)
    print("CONTRACT ADDRESS UPDATE SCRIPT V2 - Match by Ticker")
    print("="*80)
    
    # Get tokens from Supabase
    tokens = get_all_tokens_from_supabase()
    print(f"✅ Found {len(tokens)} total tokens with contract addresses")
    
    # Create mapping from ticker to contract info
    # Use a dict to store the first occurrence of each ticker
    ticker_to_contract = {}
    for token in tokens:
        ticker = token['ticker'].upper()  # Normalize to uppercase
        # Only store if we haven't seen this ticker before
        if ticker not in ticker_to_contract:
            ticker_to_contract[ticker] = {
                'contract': token['contract_address'],
                'network': token.get('network', 'Unknown')
            }
    
    print(f"📊 Unique tickers with contracts: {len(ticker_to_contract)}")
    
    # Connect to local database
    conn = sqlite3.connect('website_analysis_new.db')
    cursor = conn.cursor()
    
    # Get all analyzed websites
    cursor.execute("SELECT id, ticker, url FROM website_analysis WHERE ticker IS NOT NULL")
    rows = cursor.fetchall()
    
    print(f"\n🔍 Checking {len(rows)} analyzed websites...")
    
    updated = 0
    matched = 0
    missing_tickers = []
    
    for row_id, ticker, url in rows:
        if not ticker:
            continue
            
        # Normalize ticker
        ticker_normalized = ticker.upper().strip()
        
        # Try to match by ticker
        if ticker_normalized in ticker_to_contract:
            contract_info = ticker_to_contract[ticker_normalized]
            cursor.execute(
                "UPDATE website_analysis SET contract_address = ? WHERE id = ?",
                (contract_info['contract'], row_id)
            )
            updated += 1
            matched += 1
            print(f"  ✅ {ticker}: {contract_info['contract'][:30]}... ({contract_info['network']})")
        else:
            # Try with $ prefix removed if present
            if ticker_normalized.startswith('$'):
                alt_ticker = ticker_normalized[1:]
                if alt_ticker in ticker_to_contract:
                    contract_info = ticker_to_contract[alt_ticker]
                    cursor.execute(
                        "UPDATE website_analysis SET contract_address = ? WHERE id = ?",
                        (contract_info['contract'], row_id)
                    )
                    updated += 1
                    matched += 1
                    print(f"  ✅ {ticker}: {contract_info['contract'][:30]}... (matched as {alt_ticker})")
                else:
                    missing_tickers.append(ticker)
            else:
                missing_tickers.append(ticker)
    
    conn.commit()
    
    # Now show which ones are missing
    if missing_tickers:
        print(f"\n❌ Tickers not found in Supabase ({len(missing_tickers)}):")
        for ticker in missing_tickers[:20]:  # Show first 20
            print(f"  - {ticker}")
        if len(missing_tickers) > 20:
            print(f"  ... and {len(missing_tickers) - 20} more")
    
    conn.close()
    
    print(f"\n📈 Summary:")
    print(f"  - Total websites analyzed: {len(rows)}")
    print(f"  - Contract addresses found: {matched}")
    print(f"  - Database records updated: {updated}")
    print(f"  - Coverage: {matched/len(rows)*100:.1f}%")
    print(f"  - Missing: {len(missing_tickers)} tokens")
    
    print("\n✨ Contract addresses updated successfully!")

if __name__ == '__main__':
    main()