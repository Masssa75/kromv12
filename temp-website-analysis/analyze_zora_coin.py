#!/usr/bin/env python3
"""
Analyze the zoraCoin parameter and IPFS URL structure
"""

import requests
import json

def analyze_zora_connection():
    """
    Investigate the Zora/IPFS connection
    """
    
    # The mysterious URL components
    ipfs_hash = "bafybeibu7zfemd772ssqs6b2ok3cp3pp3usigdgepcvtfq4idxq3y6rf6m"
    contract = "0x885a590198e5f0947f4c92db815cf2a2147980b8"
    full_url = f"https://tba-social.mypinata.cloud/ipfs/{ipfs_hash}?zoraCoin={contract}"
    
    print("=" * 70)
    print("ANALYZING ZORA COIN PARAMETER")
    print("=" * 70)
    print(f"Contract: {contract}")
    print(f"IPFS Hash: {ipfs_hash}")
    print(f"Full URL: {full_url}")
    print()
    
    # Check what this IPFS content is
    print("Checking IPFS content...")
    try:
        response = requests.get(full_url, timeout=10)
        content_type = response.headers.get('content-type', 'unknown')
        print(f"Content-Type: {content_type}")
        print(f"Status: {response.status_code}")
        
        if 'image' in content_type:
            print("✓ This is an IMAGE file (likely NFT artwork)")
        elif 'json' in content_type:
            print("✓ This is JSON metadata")
            print(json.dumps(response.json(), indent=2)[:500])
        else:
            print(f"Content preview: {response.text[:200]}")
    except Exception as e:
        print(f"Error fetching IPFS: {e}")
    
    print("\n" + "=" * 70)
    print("POSSIBLE EXPLANATIONS")
    print("=" * 70)
    
    print("""
1. ZORA MINT REFERRAL SYSTEM:
   - Zora is an NFT platform on Base/Ethereum
   - The 'zoraCoin' parameter might be a referral/reward mechanism
   - When someone mints through this link, rewards go to that contract
   
2. BASESHAKE TOKEN CONNECTION:
   - BASESHAKE (0x885a59...) is a Base chain memecoin
   - Someone may have hijacked Brian Armstrong's post URL
   - Added the zoraCoin parameter to associate their token with his post
   
3. MINTING REWARDS:
   - The contract could be receiving mint rewards from Zora
   - This creates an association between the token and the post
   
4. URL MANIPULATION:
   - The original post: "just setting up my base"
   - Someone added ?zoraCoin= parameter later
   - Farcaster might preserve URL parameters in shares/embeds
    """)
    
    print("=" * 70)
    print("VERIFICATION")
    print("=" * 70)
    
    # Check if URL works without the parameter
    clean_url = f"https://tba-social.mypinata.cloud/ipfs/{ipfs_hash}"
    print(f"Testing clean URL (no zoraCoin): {clean_url}")
    
    try:
        response = requests.head(clean_url, timeout=5)
        if response.status_code == 200:
            print("✓ IPFS content exists WITHOUT the zoraCoin parameter")
            print("→ This confirms zoraCoin is just an optional parameter")
    except:
        pass
    
    # Try to understand the timeline
    print("\n" + "=" * 70)
    print("LIKELY SCENARIO")
    print("=" * 70)
    print("""
Most likely explanation:
1. Brian Armstrong posted "just setting up my base" with an NFT/image
2. The image is hosted on IPFS (common for NFTs)
3. Someone created BASESHAKE token inspired by this famous post
4. They added ?zoraCoin=<their-contract> to the URL
5. This parameter doesn't affect the image but creates an on-chain association
6. When shared/embedded, Farcaster preserves the full URL with parameter
7. The CA verification system found this embedded parameter

This is actually clever marketing:
- Associates their token with Brian Armstrong's famous Base post
- The parameter is invisible to users but detectable by scrapers
- Creates a "legitimate" connection without being obviously fake
    """)

if __name__ == "__main__":
    analyze_zora_connection()