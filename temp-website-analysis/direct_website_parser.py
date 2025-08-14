#!/usr/bin/env python3
"""
Direct website parser - No AI needed, just fetch and search
Much more reliable than AI models trying to do searches
"""

import requests
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import time
import sqlite3
from datetime import datetime

def fetch_and_search(website_url, contract_address, timeout=10):
    """
    Directly fetch website and search for contract address
    Returns dict with verification results
    """
    
    result = {
        'website_url': website_url,
        'contract_address': contract_address,
        'found': False,
        'locations': [],
        'error': None,
        'html_size': 0
    }
    
    try:
        # Normalize contract address (remove 0x prefix for flexibility)
        contract_normalized = contract_address.lower()
        contract_no_prefix = contract_normalized.replace('0x', '')
        
        # Fetch the website
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(website_url, headers=headers, timeout=timeout)
        response.raise_for_status()
        
        html_content = response.text
        result['html_size'] = len(html_content)
        
        # Parse HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Get all text content (removes HTML tags)
        text_content = soup.get_text().lower()
        
        # Search strategies:
        # 1. Look for exact contract address
        if contract_normalized in text_content:
            result['found'] = True
            result['locations'].append('body_text')
        
        # 2. Look for contract without 0x prefix
        if contract_no_prefix in text_content and len(contract_no_prefix) > 20:
            result['found'] = True
            result['locations'].append('body_text_no_prefix')
        
        # 3. Check specific HTML elements where contracts often appear
        # Check links
        for link in soup.find_all('a', href=True):
            href = link['href'].lower()
            if contract_normalized in href or contract_no_prefix in href:
                result['found'] = True
                result['locations'].append(f'link_href')
                break
        
        # Check meta tags
        for meta in soup.find_all('meta'):
            content = str(meta.get('content', '')).lower()
            if contract_normalized in content or contract_no_prefix in content:
                result['found'] = True
                result['locations'].append('meta_tag')
                break
        
        # Check scripts (often contracts are in JavaScript)
        for script in soup.find_all('script'):
            script_text = str(script.string or '').lower()
            if contract_normalized in script_text or contract_no_prefix in script_text:
                result['found'] = True
                result['locations'].append('javascript')
                break
        
        # Check data attributes
        for elem in soup.find_all(attrs={'data-contract': True}):
            if contract_normalized in str(elem.get('data-contract', '')).lower():
                result['found'] = True
                result['locations'].append('data_attribute')
                break
        
        # Check for copy buttons (common pattern)
        for elem in soup.find_all(class_=re.compile(r'copy|contract|address', re.I)):
            elem_text = elem.get_text().lower()
            if contract_normalized in elem_text or contract_no_prefix in elem_text:
                result['found'] = True
                result['locations'].append('copy_element')
                break
        
    except requests.RequestException as e:
        result['error'] = f"Request failed: {str(e)[:100]}"
    except Exception as e:
        result['error'] = f"Parse error: {str(e)[:100]}"
    
    return result

def verify_token(ticker, network, contract, website):
    """
    Verify a single token by directly checking its website
    """
    print(f"\nVerifying {ticker} on {network}")
    print(f"  Contract: {contract[:20]}...")
    print(f"  Website: {website}")
    
    # Parse the website
    result = fetch_and_search(website, contract)
    
    if result['error']:
        print(f"  ❌ Error: {result['error']}")
        verdict = 'ERROR'
    elif result['found']:
        print(f"  ✅ FOUND - Contract appears on website")
        print(f"  Locations: {', '.join(result['locations'])}")
        verdict = 'LEGITIMATE'
    else:
        print(f"  🚫 NOT FOUND - Contract not on website")
        verdict = 'FAKE'
    
    result['verdict'] = verdict
    return result

def test_known_tokens():
    """
    Test on tokens we know the correct answer for
    """
    test_cases = [
        {
            'ticker': 'VOCL',
            'network': 'ethereum',
            'contract': '0xfEa2e874C0d06031E65ea7E275070e207c2746Fd',
            'website': 'https://vocalad.ai/',
            'expected': 'LEGITIMATE'  # Contract IS in footer
        },
        {
            'ticker': 'GRAY',
            'network': 'ethereum', 
            'contract': '0xa776A95223C500E81Cb0937B291140fF550ac3E4',
            'website': 'https://www.gradient.trade/',
            'expected': 'FAKE'  # Contract NOT on website
        },
        {
            'ticker': 'TREN',
            'network': 'base',
            'contract': '0xa77E22bFAeE006D4f9DC2c20D7D337b05125C282',
            'website': 'https://www.tren.finance/',
            'expected': 'LEGITIMATE'  # Contract in docs
        },
        {
            'ticker': 'ETHEREUM',
            'network': 'ethereum',
            'contract': '0x788A4C13A8945B15E2009D4526A3d4aBdB81928D',
            'website': 'https://ultrasound.money/',
            'expected': 'FAKE'  # Impersonator token
        }
    ]
    
    print("="*60)
    print("DIRECT WEBSITE PARSING TEST")
    print("="*60)
    print("\nNo AI needed - just fetch HTML and search for contract\n")
    
    correct = 0
    for token in test_cases:
        result = verify_token(
            token['ticker'],
            token['network'],
            token['contract'],
            token['website']
        )
        
        if result['verdict'] == token['expected']:
            correct += 1
            print(f"  ✅ Correct! Expected {token['expected']}")
        else:
            print(f"  ❌ Wrong! Expected {token['expected']}, got {result['verdict']}")
        
        time.sleep(1)  # Be nice to servers
    
    print(f"\n{'='*60}")
    print(f"Accuracy: {correct}/{len(test_cases)} = {correct/len(test_cases)*100:.0f}%")
    print("="*60)

def verify_top20():
    """
    Verify top 20 tokens from database using direct parsing
    """
    conn = sqlite3.connect('analysis_results.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT DISTINCT ticker, network, contract_address, website_url 
        FROM website_analysis 
        WHERE website_url IS NOT NULL 
        ORDER BY website_score DESC 
        LIMIT 20
    """)
    
    tokens = cursor.fetchall()
    conn.close()
    
    print("\n" + "="*60)
    print("VERIFYING TOP 20 TOKENS - DIRECT PARSING")
    print("="*60)
    
    results = []
    for ticker, network, contract, website in tokens:
        result = verify_token(ticker, network, contract, website)
        results.append(result)
        time.sleep(1)
    
    # Summary
    legitimate = sum(1 for r in results if r['verdict'] == 'LEGITIMATE')
    fake = sum(1 for r in results if r['verdict'] == 'FAKE')
    errors = sum(1 for r in results if r['verdict'] == 'ERROR')
    
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"Legitimate: {legitimate}")
    print(f"Fake: {fake}")
    print(f"Errors: {errors}")
    print(f"Success rate: {(legitimate + fake)/len(results)*100:.0f}%")
    print("="*60)

if __name__ == "__main__":
    # First test on known tokens
    test_known_tokens()
    
    # Then run on top 20
    print("\n" + "="*80)
    input("Press Enter to verify top 20 tokens...")
    verify_top20()