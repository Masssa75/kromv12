#!/usr/bin/env python3
"""
Verify a sample of LEGITIMATE tokens to test system accuracy
"""

import requests
from bs4 import BeautifulSoup
import time

# Sample of LEGITIMATE tokens to verify
test_tokens = [
    {
        "ticker": "PEPE",
        "contract": "EkJuyYyD3to61CHVPJn6wHb7xANxvqApnVJ4o2SdBAGS",
        "website": "https://bags.fm/EkJuyYyD3to61CHVPJn6wHb7xANxvqApnVJ4o2SdBAGS",
        "found_at": "https://bags.fm/EkJuyYyD3to61CHVPJn6wHb7xANxvqApnVJ4o2SdBAGS"
    },
    {
        "ticker": "BLOB",
        "contract": "6qHtAvksH2cSaUjz6euVSikPU8RnDqLpFtuWH6Ropump",
        "website": "https://blobisbob.com/",
        "found_at": "https://blobisbob.com/"
    },
    {
        "ticker": "DEAL",
        "contract": "EdhCrv9wh2dVy7LwA4kZ3pvBRhSXzhPrYeVqX7VcsmbS",
        "website": "https://dealwith.it.com",
        "found_at": "https://dealwith.it.com"
    },
    {
        "ticker": "POPCAT",
        "contract": "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr",
        "website": "https://www.popcatsolana.xyz/",
        "found_at": "https://www.popcatsolana.xyz/"
    },
    {
        "ticker": "QBIT",
        "contract": "0xB17bE9A85D1e04D1aA6eA4b83C0bb6A2030c261F",
        "website": "https://qbit.technology/",
        "found_at": "https://qbit.technology/"
    }
]

def check_contract_on_website(url, contract):
    """Check if contract appears on website"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
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
    print("VERIFYING LEGITIMATE TOKENS")
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