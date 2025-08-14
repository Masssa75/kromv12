#!/usr/bin/env python3
"""
Verify second batch of LEGITIMATE tokens
"""

import requests
from bs4 import BeautifulSoup
import time

# Second batch of LEGITIMATE tokens to verify
test_tokens = [
    {
        "ticker": "CRYBB",
        "contract": "FP2XnGpqP5opNZujB6KPpXYWSAwq7BbTUVUnRij1bonk",
        "website": "https://crybaby.meme",
        "found_at": "https://crybaby.meme"
    },
    {
        "ticker": "CLIPPY",
        "contract": "7eMJmn1bYWSQEwxAX7CyngBzGNGu1cT582asKxxRpump",
        "website": "https://www.clippycult.xyz",
        "found_at": "https://www.clippycult.xyz"
    },
    {
        "ticker": "BILLY",
        "contract": "0xeb560289067c375E4897552DCDA7E3d203BFFBE2",
        "website": "https://www.basechainbilly.xyz/",
        "found_at": "https://www.basechainbilly.xyz/"
    },
    {
        "ticker": "BEAST",
        "contract": "0x255494B830bd4FE7220B3ec4842CBA75600b6C80",
        "website": "https://beastseller.art/",
        "found_at": "https://beastseller.art/"
    },
    {
        "ticker": "VALENTINE",
        "contract": "9GtvcnDUvGsuibktxiMjLQ2yyBq5akUahuBs8yANbonk",
        "website": "https://link.me/valentinesol",
        "found_at": "https://link.me/valentinesol"
    }
]

def check_contract_on_website(url, contract):
    """Check if contract appears on website"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        if response.status_code != 200:
            return False, f"HTTP {response.status_code}"
        
        # Check if contract appears in page content
        content = response.text.lower()
        contract_lower = contract.lower()
        
        if contract_lower in content:
            return True, "Found in page content"
        
        # Also check without 0x prefix for Ethereum contracts
        if contract.startswith('0x'):
            if contract[2:].lower() in content:
                return True, "Found without 0x prefix"
        
        return False, "Contract not found on page"
        
    except requests.RequestException as e:
        return False, f"Error: {str(e)}"
    except Exception as e:
        return False, f"Unexpected error: {str(e)}"

def main():
    print("=" * 60)
    print("VERIFYING LEGITIMATE TOKENS (BATCH 2)")
    print("=" * 60)
    
    results = []
    
    for token in test_tokens:
        print(f"\nChecking {token['ticker']}...")
        print(f"  Contract: {token['contract'][:20]}...")
        print(f"  Website: {token['website']}")
        
        found, message = check_contract_on_website(token['website'], token['contract'])
        
        if found:
            print(f"  ✅ VERIFIED - {message}")
            results.append(True)
        else:
            print(f"  ❌ NOT FOUND - {message}")
            results.append(False)
        
        time.sleep(1)  # Be polite to servers
    
    # Calculate accuracy
    print("\n" + "=" * 60)
    print("RESULTS SUMMARY")
    print("=" * 60)
    
    correct = sum(results)
    total = len(results)
    accuracy = (correct / total) * 100 if total > 0 else 0
    
    print(f"Tokens tested: {total}")
    print(f"Correctly verified: {correct}")
    print(f"Incorrectly marked as legitimate: {total - correct}")
    print(f"Accuracy rate: {accuracy:.1f}%")
    
    if accuracy >= 80:
        print("\n✅ System reliability: HIGH")
    elif accuracy >= 60:
        print("\n⚠️ System reliability: MODERATE")
    else:
        print("\n❌ System reliability: LOW")

if __name__ == "__main__":
    main()