#!/usr/bin/env python3
"""
Comprehensive verification of 40 LEGITIMATE tokens
"""

import requests
import time
import sqlite3

def check_contract_on_website(url, contract, ticker):
    """Check if contract appears on website"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        if response.status_code != 200:
            return False, f"HTTP {response.status_code}", None
        
        # Check if contract appears in page content
        content = response.text.lower()
        contract_lower = contract.lower()
        
        if contract_lower in content:
            # Find the position for context
            pos = content.find(contract_lower)
            context = content[max(0, pos-50):pos+len(contract_lower)+50]
            return True, "Found in page content", context
        
        # Also check without 0x prefix for Ethereum contracts
        if contract.startswith('0x'):
            if contract[2:].lower() in content:
                pos = content.find(contract[2:].lower())
                context = content[max(0, pos-50):pos+len(contract)+50]
                return True, "Found without 0x prefix", context
        
        return False, "Contract not found on page", None
        
    except requests.Timeout:
        return False, "Timeout", None
    except requests.RequestException as e:
        return False, f"Error: {str(e)[:50]}", None
    except Exception as e:
        return False, f"Unexpected: {str(e)[:50]}", None

def main():
    # Get all 40 tokens from database
    conn = sqlite3.connect('utility_tokens_ca.db')
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT ticker, network, contract_address, website_url 
        FROM ca_verification_results 
        WHERE verdict='LEGITIMATE' 
        ORDER BY ticker 
        LIMIT 40
    """)
    
    tokens = cursor.fetchall()
    conn.close()
    
    print("=" * 70)
    print("COMPREHENSIVE VERIFICATION OF 40 LEGITIMATE TOKENS")
    print("=" * 70)
    
    results = []
    incorrect_tokens = []
    
    for i, (ticker, network, contract, website) in enumerate(tokens, 1):
        print(f"\n[{i}/40] Checking {ticker} ({network})...")
        print(f"  Contract: {contract[:30]}...")
        print(f"  Website: {website}")
        
        found, message, context = check_contract_on_website(website, contract, ticker)
        
        if found:
            print(f"  ✅ VERIFIED - {message}")
            results.append(True)
        else:
            print(f"  ❌ NOT FOUND - {message}")
            results.append(False)
            incorrect_tokens.append({
                'ticker': ticker,
                'network': network,
                'contract': contract,
                'website': website,
                'reason': message
            })
        
        # Progress indicator every 10 tokens
        if i % 10 == 0:
            current_accuracy = (sum(results) / len(results)) * 100
            print(f"\n--- Progress: {i}/40 tokens checked | Current accuracy: {current_accuracy:.1f}% ---")
        
        # Be polite to servers
        time.sleep(0.5)
    
    # Final summary
    print("\n" + "=" * 70)
    print("FINAL RESULTS SUMMARY")
    print("=" * 70)
    
    correct = sum(results)
    total = len(results)
    accuracy = (correct / total) * 100 if total > 0 else 0
    
    print(f"\nTokens tested: {total}")
    print(f"Correctly verified: {correct}")
    print(f"Incorrectly marked as legitimate: {total - correct}")
    print(f"ACCURACY RATE: {accuracy:.1f}%")
    
    if accuracy >= 90:
        print("\n✅ VERDICT: HIGHLY RELIABLE - The 'LEGITIMATE' classification is very accurate")
    elif accuracy >= 80:
        print("\n✅ VERDICT: RELIABLE - The 'LEGITIMATE' classification is trustworthy")
    elif accuracy >= 70:
        print("\n⚠️ VERDICT: MODERATELY RELIABLE - Some false positives exist")
    else:
        print("\n❌ VERDICT: UNRELIABLE - Too many false positives")
    
    # List incorrect classifications
    if incorrect_tokens:
        print("\n" + "=" * 70)
        print("INCORRECTLY CLASSIFIED AS LEGITIMATE:")
        print("=" * 70)
        for token in incorrect_tokens:
            print(f"\n❌ {token['ticker']} ({token['network']})")
            print(f"   Contract: {token['contract']}")
            print(f"   Website: {token['website']}")
            print(f"   Issue: {token['reason']}")
    
    # Save results to file for manual review
    with open('legitimate_verification_results.txt', 'w') as f:
        f.write(f"Verification Results for 40 LEGITIMATE Tokens\n")
        f.write(f"Accuracy: {accuracy:.1f}%\n")
        f.write(f"Correct: {correct}/{total}\n\n")
        
        if incorrect_tokens:
            f.write("Tokens that need manual review:\n")
            for token in incorrect_tokens:
                f.write(f"{token['ticker']},{token['network']},{token['contract']},{token['website']},{token['reason']}\n")
    
    print("\n📄 Results saved to: legitimate_verification_results.txt")

if __name__ == "__main__":
    main()