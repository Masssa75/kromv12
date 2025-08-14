#!/usr/bin/env python3
"""
Verify FAKE tokens to ensure they truly don't have contracts on their websites
"""

import requests
from bs4 import BeautifulSoup
import time

# Sample of FAKE tokens to verify
test_tokens = [
    {
        "ticker": "MAMO",
        "contract": "0x7300B37DfdfAb110d83290A29DfB31B1740219fE",
        "website": "https://mamo.bot/"
    },
    {
        "ticker": "KOLSCAN",
        "contract": "6jTQCFZR8JwvvenVGa3RzGM3a5YEagk9kQXDpHHdpump",
        "website": "https://kolscan.io"
    },
    {
        "ticker": "FARTCOIN",
        "contract": "9BB6NFEcjBCtnNLFko2FqVQBq8HHM13kCyYcdQbgpump",
        "website": "https://www.infinitebackrooms.com/dreams/conversation-1721540624-scenario-terminal-of-truths-txt"
    },
    {
        "ticker": "BLOCK",
        "contract": "0xCaB84bc21F9092167fCFe0ea60f5CE053ab39a1E",
        "website": "https://www.blockstreet.xyz/"
    },
    {
        "ticker": "GOB",
        "contract": "3xypwTgs9nWgjc6nUBiHmMb36t2PwL3SwCZkEQvW8FTX",
        "website": "https://www.gob.wtf/"
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
    print("VERIFYING FAKE TOKENS")
    print("=" * 60)
    print("These should NOT have contracts on their websites")
    
    results = []
    
    for token in test_tokens:
        print(f"\nChecking {token['ticker']}...")
        print(f"  Contract: {token['contract'][:20]}...")
        print(f"  Website: {token['website']}")
        
        found, message = check_contract_on_website(token['website'], token['contract'])
        
        if not found:
            print(f"  ✅ CORRECTLY IDENTIFIED AS FAKE - {message}")
            results.append(True)
        else:
            print(f"  ❌ INCORRECTLY MARKED AS FAKE - {message}")
            print(f"     (Contract WAS found on website!)")
            results.append(False)
        
        time.sleep(1)  # Be polite to servers
    
    # Calculate accuracy
    print("\n" + "=" * 60)
    print("FAKE TOKEN VERIFICATION SUMMARY")
    print("=" * 60)
    
    correct = sum(results)
    total = len(results)
    accuracy = (correct / total) * 100 if total > 0 else 0
    
    print(f"Tokens tested: {total}")
    print(f"Correctly identified as fake: {correct}")
    print(f"Incorrectly marked as fake: {total - correct}")
    print(f"Accuracy rate: {accuracy:.1f}%")
    
    if accuracy >= 80:
        print("\n✅ System reliability for FAKE detection: HIGH")
    elif accuracy >= 60:
        print("\n⚠️ System reliability for FAKE detection: MODERATE")
    else:
        print("\n❌ System reliability for FAKE detection: LOW")

if __name__ == "__main__":
    main()