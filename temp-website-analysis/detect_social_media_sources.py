#!/usr/bin/env python3
"""
Detect and flag social media sources in CA verification results
"""

import sqlite3
from urllib.parse import urlparse

# Social media domains and platforms
SOCIAL_MEDIA_DOMAINS = {
    'twitter.com': 'Twitter',
    'x.com': 'X (Twitter)',
    'facebook.com': 'Facebook',
    'instagram.com': 'Instagram',
    'reddit.com': 'Reddit',
    'linkedin.com': 'LinkedIn',
    'telegram.org': 'Telegram',
    't.me': 'Telegram',
    'discord.com': 'Discord',
    'discord.gg': 'Discord',
    'youtube.com': 'YouTube',
    'tiktok.com': 'TikTok',
    'medium.com': 'Medium',
    'substack.com': 'Substack',
    'farcaster.xyz': 'Farcaster',
    'warpcast.com': 'Warpcast',
    'lens.xyz': 'Lens Protocol',
    'mirror.xyz': 'Mirror',
    'paragraph.xyz': 'Paragraph',
}

def detect_source_type(url):
    """
    Detect if URL is a social media platform or regular website
    Returns: (source_type, platform_name, warning_message)
    """
    if not url or url == 'None':
        return 'no_website', None, None
    
    try:
        parsed = urlparse(url.lower())
        domain = parsed.netloc.replace('www.', '')
        
        # Check if it's a social media platform
        for social_domain, platform in SOCIAL_MEDIA_DOMAINS.items():
            if social_domain in domain:
                warning = f"Contract found on {platform} post - not an official website"
                return 'social_media', platform, warning
        
        # Check for other suspicious patterns
        if 'ipfs' in domain or 'pinata' in domain:
            return 'ipfs', 'IPFS', "Contract found in IPFS metadata"
        
        if any(x in parsed.path for x in ['/status/', '/post/', '/tweet/', '/cast/']):
            return 'social_post', 'Social Post', "Contract found in social media post"
        
        # Default to website
        return 'website', None, None
        
    except Exception as e:
        print(f"Error parsing URL {url}: {e}")
        return 'unknown', None, None

def update_database():
    """
    Update all existing records with source type and warnings
    """
    conn = sqlite3.connect('utility_tokens_ca.db')
    cursor = conn.cursor()
    
    # Get all records
    cursor.execute("SELECT ticker, network, contract_address, website_url FROM ca_verification_results")
    records = cursor.fetchall()
    
    print("=" * 70)
    print("DETECTING SOCIAL MEDIA SOURCES")
    print("=" * 70)
    
    social_count = 0
    website_count = 0
    no_website_count = 0
    
    for ticker, network, contract, url in records:
        source_type, platform, warning = detect_source_type(url)
        
        # Update the record
        cursor.execute("""
            UPDATE ca_verification_results 
            SET source_type = ?, warning_flags = ?
            WHERE ticker = ? AND network = ? AND contract_address = ?
        """, (source_type, warning, ticker, network, contract))
        
        if source_type == 'social_media' or source_type == 'social_post':
            social_count += 1
            print(f"⚠️  {ticker}: {platform} - {url[:50]}...")
        elif source_type == 'website':
            website_count += 1
        else:
            no_website_count += 1
    
    conn.commit()
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total tokens: {len(records)}")
    print(f"Official websites: {website_count}")
    print(f"Social media sources: {social_count}")
    print(f"No website: {no_website_count}")
    
    # Show all social media tokens that are marked as LEGITIMATE
    cursor.execute("""
        SELECT ticker, network, website_url, warning_flags 
        FROM ca_verification_results 
        WHERE verdict = 'LEGITIMATE' 
        AND source_type IN ('social_media', 'social_post')
    """)
    
    social_legitimate = cursor.fetchall()
    if social_legitimate:
        print("\n" + "=" * 70)
        print("⚠️  LEGITIMATE TOKENS FROM SOCIAL MEDIA (Need Review)")
        print("=" * 70)
        for ticker, network, url, warning in social_legitimate:
            print(f"{ticker} ({network}): {warning}")
            print(f"  URL: {url}")
    
    conn.close()
    print("\n✅ Database updated with source type detection")

if __name__ == "__main__":
    update_database()