#!/usr/bin/env python3
"""
Analyze liquidity patterns to identify potential fake/scam tokens
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# Load environment variables
load_dotenv()

# Supabase credentials
url = os.getenv("SUPABASE_URL")
service_role_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Initialize Supabase client with service role key
supabase: Client = create_client(url, service_role_key)

def analyze_liquidity_patterns():
    """Analyze liquidity patterns across all tokens"""
    
    print("=" * 80)
    print("LIQUIDITY PATTERN ANALYSIS")
    print("=" * 80)
    
    # First, let's check the BLOCK token specifically
    print("\n1. CHECKING BLOCK TOKEN (suspected fake):")
    print("-" * 40)
    
    block_response = supabase.table('crypto_calls').select(
        'ticker, network, contract_address, liquidity_usd, liquidity_locked, '
        'liquidity_lock_percent, current_price, market_cap_at_call, current_market_cap, '
        'roi_percent, ath_roi_percent, security_score'
    ).eq('ticker', 'BLOCK').execute()
    
    if block_response.data:
        for token in block_response.data:
            print(f"Token: {token['ticker']} ({token['network']})")
            print(f"Contract: {token['contract_address']}")
            print(f"Liquidity: ${token['liquidity_usd']:,.0f}" if token['liquidity_usd'] else "Liquidity: Unknown")
            print(f"Liquidity Locked: {token['liquidity_locked']}")
            print(f"Lock Percent: {token['liquidity_lock_percent']}%")
            print(f"Security Score: {token['security_score']}")
            print()
    
    # Get all tokens with liquidity data
    print("\n2. ANALYZING ALL TOKENS WITH LIQUIDITY DATA:")
    print("-" * 40)
    
    response = supabase.table('crypto_calls').select(
        'ticker, network, contract_address, liquidity_usd, liquidity_locked, '
        'liquidity_lock_percent, current_price, market_cap_at_call, current_market_cap, '
        'roi_percent, ath_roi_percent, security_score, is_coin_of_interest'
    ).not_.is_('liquidity_usd', 'null').execute()
    
    df = pd.DataFrame(response.data)
    
    if not df.empty:
        # Basic statistics
        print(f"Total tokens with liquidity data: {len(df)}")
        print(f"Average liquidity: ${df['liquidity_usd'].mean():,.0f}")
        print(f"Median liquidity: ${df['liquidity_usd'].median():,.0f}")
        
        # Categorize by liquidity levels
        print("\n3. LIQUIDITY DISTRIBUTION:")
        print("-" * 40)
        
        # Define liquidity categories
        df['liquidity_category'] = pd.cut(
            df['liquidity_usd'],
            bins=[0, 1000, 10000, 50000, 100000, 500000, 1000000, float('inf')],
            labels=['<$1K', '$1K-10K', '$10K-50K', '$50K-100K', '$100K-500K', '$500K-1M', '>$1M']
        )
        
        category_counts = df['liquidity_category'].value_counts().sort_index()
        for category, count in category_counts.items():
            print(f"{category}: {count} tokens ({count/len(df)*100:.1f}%)")
        
        # Analyze liquidity lock patterns
        print("\n4. LIQUIDITY LOCK ANALYSIS:")
        print("-" * 40)
        
        # Filter for tokens with lock data
        df_with_lock = df[df['liquidity_locked'].notna()]
        
        if not df_with_lock.empty:
            locked = df_with_lock[df_with_lock['liquidity_locked'] == True]
            unlocked = df_with_lock[df_with_lock['liquidity_locked'] == False]
            
            print(f"Tokens with lock data: {len(df_with_lock)}")
            print(f"Locked liquidity: {len(locked)} ({len(locked)/len(df_with_lock)*100:.1f}%)")
            print(f"Unlocked liquidity: {len(unlocked)} ({len(unlocked)/len(df_with_lock)*100:.1f}%)")
            
            # Average liquidity by lock status
            if not locked.empty:
                print(f"\nAverage liquidity (LOCKED): ${locked['liquidity_usd'].mean():,.0f}")
            if not unlocked.empty:
                print(f"Average liquidity (UNLOCKED): ${unlocked['liquidity_usd'].mean():,.0f}")
        
        # Find suspicious patterns
        print("\n5. SUSPICIOUS PATTERNS (Red Flags):")
        print("-" * 40)
        
        # High liquidity but unlocked
        high_liq_unlocked = df[
            (df['liquidity_usd'] > 100000) & 
            (df['liquidity_locked'] == False)
        ].sort_values('liquidity_usd', ascending=False)
        
        if not high_liq_unlocked.empty:
            print(f"\n🚨 HIGH LIQUIDITY + UNLOCKED ({len(high_liq_unlocked)} tokens):")
            for _, token in high_liq_unlocked.head(10).iterrows():
                print(f"   {token['ticker']}: ${token['liquidity_usd']:,.0f} (unlocked)")
                if token['security_score']:
                    print(f"      Security Score: {token['security_score']}")
        
        # Very low liquidity (potential rug pull risk)
        very_low_liq = df[df['liquidity_usd'] < 1000]
        print(f"\n⚠️ VERY LOW LIQUIDITY (<$1K): {len(very_low_liq)} tokens")
        
        # High market cap but low liquidity (suspicious)
        if 'current_market_cap' in df.columns:
            df['mcap_to_liq_ratio'] = df['current_market_cap'] / df['liquidity_usd']
            suspicious_ratio = df[
                (df['mcap_to_liq_ratio'] > 100) & 
                (df['current_market_cap'] > 100000)
            ].sort_values('mcap_to_liq_ratio', ascending=False)
            
            if not suspicious_ratio.empty:
                print(f"\n🚨 HIGH MCAP/LIQUIDITY RATIO (>100x):")
                for _, token in suspicious_ratio.head(10).iterrows():
                    print(f"   {token['ticker']}: MCap ${token['current_market_cap']:,.0f} / Liq ${token['liquidity_usd']:,.0f} = {token['mcap_to_liq_ratio']:.0f}x")
        
        # Tokens with best liquidity profiles
        print("\n6. BEST LIQUIDITY PROFILES:")
        print("-" * 40)
        
        best_profiles = df[
            (df['liquidity_usd'] > 50000) & 
            (df['liquidity_locked'] == True) &
            (df['liquidity_lock_percent'] > 50)
        ].sort_values('liquidity_usd', ascending=False)
        
        if not best_profiles.empty:
            print(f"✅ HIGH LIQUIDITY + LOCKED ({len(best_profiles)} tokens):")
            for _, token in best_profiles.head(10).iterrows():
                print(f"   {token['ticker']}: ${token['liquidity_usd']:,.0f} ({token['liquidity_lock_percent']:.0f}% locked)")
        
        # Summary recommendations
        print("\n7. LIQUIDITY-BASED QUALITY INDICATORS:")
        print("-" * 40)
        print("✅ GREEN FLAGS:")
        print("   - Liquidity > $50K")
        print("   - Liquidity locked > 50%")
        print("   - MCap/Liquidity ratio < 20")
        print("\n🚨 RED FLAGS:")
        print("   - High liquidity (>$100K) but unlocked")
        print("   - MCap/Liquidity ratio > 100")
        print("   - Liquidity < $1K")
        print("   - No liquidity data available")
        
        return df

if __name__ == "__main__":
    df = analyze_liquidity_patterns()