#!/usr/bin/env python3
"""
Compare liquidity patterns between verified legitimate vs fake tokens
"""

import os
import sqlite3
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Supabase credentials
url = os.getenv("SUPABASE_URL")
service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Initialize Supabase client
supabase: Client = create_client(url, service_role_key)

def compare_liquidity_patterns():
    """Compare liquidity between legitimate and fake tokens"""
    
    print("=" * 80)
    print("LIQUIDITY COMPARISON: LEGITIMATE vs FAKE TOKENS")
    print("=" * 80)
    
    # Connect to utility tokens database
    conn = sqlite3.connect('temp-website-analysis/utility_tokens_ca.db')
    cursor = conn.cursor()
    
    # Get all verified tokens
    cursor.execute("""
        SELECT ticker, network, contract_address, verdict
        FROM ca_verification_results
        WHERE verdict IN ('LEGITIMATE', 'FAKE')
    """)
    
    ca_results = cursor.fetchall()
    conn.close()
    
    legitimate_tickers = [r[0] for r in ca_results if r[3] == 'LEGITIMATE']
    fake_tickers = [r[0] for r in ca_results if r[3] == 'FAKE']
    
    print(f"\nTokens from CA verification:")
    print(f"Legitimate: {len(legitimate_tickers)}")
    print(f"Fake: {len(fake_tickers)}")
    
    # Get liquidity data for these tokens from Supabase
    print("\n" + "=" * 80)
    print("LIQUIDITY ANALYSIS FOR VERIFIED TOKENS")
    print("=" * 80)
    
    # Get legitimate tokens liquidity
    if legitimate_tickers:
        leg_response = supabase.table('crypto_calls').select(
            'ticker, network, liquidity_usd, liquidity_locked, '
            'liquidity_lock_percent, current_market_cap, security_score'
        ).in_('ticker', legitimate_tickers[:50]).execute()  # Limit to first 50
        
        print("\n✅ LEGITIMATE TOKENS (Sample):")
        print("-" * 40)
        
        high_liq_unlocked = []
        low_liquidity = []
        good_profile = []
        
        for token in leg_response.data:
            liq = token.get('liquidity_usd', 0) or 0
            locked = token.get('liquidity_locked', None)
            
            if liq > 100000 and locked == False:
                high_liq_unlocked.append(token)
            elif liq < 10000 and liq > 0:
                low_liquidity.append(token)
            elif liq > 50000 and locked == True:
                good_profile.append(token)
        
        if high_liq_unlocked:
            print(f"\n🚨 HIGH LIQUIDITY BUT UNLOCKED ({len(high_liq_unlocked)}):")
            for t in high_liq_unlocked[:5]:
                print(f"   {t['ticker']}: ${t['liquidity_usd']:,.0f} (UNLOCKED)")
        
        if good_profile:
            print(f"\n✅ GOOD LIQUIDITY PROFILE ({len(good_profile)}):")
            for t in good_profile[:5]:
                print(f"   {t['ticker']}: ${t['liquidity_usd']:,.0f} (LOCKED)")
    
    # Get fake tokens liquidity
    if fake_tickers:
        fake_response = supabase.table('crypto_calls').select(
            'ticker, network, liquidity_usd, liquidity_locked, '
            'liquidity_lock_percent, current_market_cap, security_score'
        ).in_('ticker', fake_tickers[:50]).execute()  # Limit to first 50
        
        print("\n🚫 FAKE/IMPOSTER TOKENS (Sample):")
        print("-" * 40)
        
        suspicious_patterns = []
        
        for token in fake_response.data:
            liq = token.get('liquidity_usd', 0) or 0
            locked = token.get('liquidity_locked', None)
            mcap = token.get('current_market_cap', 0) or 0
            
            # Check for suspicious patterns
            suspicious = False
            reasons = []
            
            if liq > 100000 and locked == False:
                suspicious = True
                reasons.append("High liq but unlocked")
            
            if mcap > 0 and liq > 0 and (mcap / liq) > 100:
                suspicious = True
                reasons.append(f"MCap/Liq ratio: {mcap/liq:.0f}x")
            
            if suspicious:
                suspicious_patterns.append({
                    'ticker': token['ticker'],
                    'liquidity': liq,
                    'locked': locked,
                    'reasons': reasons
                })
        
        if suspicious_patterns:
            print(f"\n🚨 SUSPICIOUS LIQUIDITY PATTERNS ({len(suspicious_patterns)}):")
            for t in suspicious_patterns[:10]:
                print(f"   {t['ticker']}: ${t['liquidity']:,.0f}")
                for reason in t['reasons']:
                    print(f"      - {reason}")
    
    # Specific check for BLOCK token
    print("\n" + "=" * 80)
    print("DEEP DIVE: BLOCK TOKEN ANALYSIS")
    print("=" * 80)
    
    block_response = supabase.table('crypto_calls').select('*').eq('ticker', 'BLOCK').execute()
    
    if block_response.data:
        for block in block_response.data:
            print(f"\nNetwork: {block['network']}")
            print(f"Contract: {block['contract_address']}")
            print(f"Liquidity: ${block.get('liquidity_usd', 0):,.0f}")
            print(f"Liquidity Locked: {block.get('liquidity_locked', 'Unknown')}")
            print(f"Market Cap: ${block.get('current_market_cap', 0):,.0f}")
            
            if block.get('liquidity_usd', 0) > 0 and block.get('current_market_cap', 0) > 0:
                ratio = block['current_market_cap'] / block['liquidity_usd']
                print(f"MCap/Liquidity Ratio: {ratio:.1f}x")
            
            # Key insight
            if block.get('liquidity_usd', 0) > 1000000 and block.get('liquidity_locked') != True:
                print("\n🚨 RED FLAG: Over $1M liquidity but NOT LOCKED!")
                print("This is highly suspicious for a token called 'BLOCK' (likely impersonating)")
    
    print("\n" + "=" * 80)
    print("KEY INSIGHTS")
    print("=" * 80)
    print("""
    1. LIQUIDITY LOCK STATUS is crucial:
       - Legitimate projects often lock liquidity
       - Scams/imposters often keep liquidity unlocked for easy rug pull
    
    2. HIGH LIQUIDITY + UNLOCKED = Major Red Flag:
       - BLOCK has $2.75M unlocked (suspicious!)
       - MAMO has $2.65M unlocked
       - These could be rug pull risks
    
    3. MCAP/LIQUIDITY RATIO:
       - Healthy ratio: < 20x
       - Suspicious: > 100x
       - Extreme cases: > 1000x (likely fake volume)
    
    4. BETTER VERIFICATION APPROACH:
       Instead of checking websites for CAs, focus on:
       ✅ Liquidity > $50K AND locked
       ✅ MCap/Liquidity ratio < 50
       ✅ Security score > 80
       ❌ High liquidity but unlocked
       ❌ Extreme MCap/Liquidity ratios
    """)

if __name__ == "__main__":
    compare_liquidity_patterns()