#!/usr/bin/env python3
"""
Process exactly 100 tokens with current price updates
FIXED VERSION: Proper Supabase query syntax and timestamp orphan avoidance
"""
import os
import sys
import requests
import time
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_ROLE_KEY = os.getenv('SUPABASE_SERVICE_ROLE_KEY')

headers = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json"
}

# Network mapping for GeckoTerminal API
NETWORK_MAP = {
    'ethereum': 'eth',
    'solana': 'solana',
    'bsc': 'bsc',
    'polygon': 'polygon',
    'arbitrum': 'arbitrum',
    'base': 'base'
}

def get_next_token():
    """Get the next token that needs a price update"""
    query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id,ticker,contract_address,network,price_at_call,current_price&contract_address=not.is.null&network=not.is.null&price_at_call=gt.0&current_price=is.null&price_updated_at=is.null&order=id.asc&limit=1"
    
    resp = requests.get(query, headers=headers)
    if resp.status_code != 200:
        print(f"❌ Query failed: {resp.status_code}")
        return None
    
    tokens = resp.json()
    if not tokens:
        return None
    
    return tokens[0]

def fetch_price_dexscreener(contract_address):
    """Try to fetch price from DexScreener"""
    try:
        resp = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}")
        if resp.status_code == 200:
            data = resp.json()
            if data.get('pairs') and len(data['pairs']) > 0:
                price = float(data['pairs'][0]['priceUsd'])
                return price, "DexScreener"
    except Exception as e:
        pass
    
    return None, None

def fetch_price_geckoterminal(contract_address, network):
    """Try to fetch price from GeckoTerminal pools"""
    try:
        api_network = NETWORK_MAP.get(network, network)
        resp = requests.get(f"https://api.geckoterminal.com/api/v2/networks/{api_network}/tokens/{contract_address}/pools")
        
        if resp.status_code == 429:
            print(f"   ⏳ Rate limited, waiting 10s...")
            time.sleep(10)
            return None, None
        
        if resp.status_code == 200:
            data = resp.json()
            pools = data.get('data', [])
            
            if pools:
                best_price = 0
                for pool in pools:
                    pool_price_str = pool['attributes'].get('token_price_usd')
                    if pool_price_str:
                        pool_price = float(pool_price_str)
                        if pool_price > best_price:
                            best_price = pool_price
                
                if best_price > 0:
                    return best_price, "GeckoTerminal"
    except Exception as e:
        pass
    
    return None, None

def update_token_price(token_id, price):
    """Update token price in database"""
    update_url = f"{SUPABASE_URL}/rest/v1/crypto_calls?id=eq.{token_id}"
    update_data = {
        "current_price": price,
        "price_updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    resp = requests.patch(update_url, json=update_data, headers=headers)
    return resp.status_code in [200, 204]

def main():
    print("🔄 Processing Next 100 Tokens")
    print("=" * 50)
    
    TARGET_COUNT = 100
    processed = 0
    successful = 0
    failed = 0
    winners = []  # Track positive ROI tokens
    
    try:
        while processed < TARGET_COUNT:
            # Get next token
            token = get_next_token()
            if not token:
                print(f"\n✅ No more tokens to process!")
                break
            
            processed += 1
            print(f"\n[{processed}/{TARGET_COUNT}] 📊 {token['ticker']} ({token['network']})")
            print(f"    CA: {token['contract_address'][:20]}...")
            print(f"    Entry: ${token['price_at_call']:.8f}")
            
            # Try DexScreener first
            price, source = fetch_price_dexscreener(token['contract_address'])
            
            # If DexScreener fails, try GeckoTerminal
            if price is None:
                price, source = fetch_price_geckoterminal(token['contract_address'], token['network'])
            
            if price:
                # Calculate ROI
                roi = ((price - token['price_at_call']) / token['price_at_call'] * 100)
                roi_symbol = "📈" if roi > 0 else "📉"
                
                # Track winners
                if roi > 0:
                    winners.append({
                        'ticker': token['ticker'],
                        'roi': roi,
                        'price': price,
                        'entry': token['price_at_call']
                    })
                
                # Update database
                if update_token_price(token['id'], price):
                    successful += 1
                    print(f"    ✅ ${price:.8f} ({source}) {roi_symbol} {roi:+.1f}%")
                else:
                    failed += 1
                    print(f"    ❌ DB update failed")
            else:
                failed += 1
                print(f"    ❌ No price found")
            
            # Progress update every 25 tokens
            if processed % 25 == 0:
                success_rate = (successful / processed) * 100
                print(f"\n📊 Progress: {processed}/{TARGET_COUNT} ({success_rate:.1f}% success, {len(winners)} winners)")
            
            # Rate limiting
            time.sleep(0.3)
    
    except KeyboardInterrupt:
        print(f"\n\n👋 Stopped by user at {processed} tokens")
    
    # Final summary
    success_rate = (successful / processed) * 100 if processed > 0 else 0
    print(f"\n📋 FINAL SUMMARY:")
    print(f"   Total processed: {processed}")
    print(f"   Successful: {successful} ({success_rate:.1f}%)")
    print(f"   Failed: {failed}")
    print(f"   Winners (positive ROI): {len(winners)}")
    
    if winners:
        print(f"\n🎉 TOP PERFORMERS:")
        winners.sort(key=lambda x: x['roi'], reverse=True)
        for i, winner in enumerate(winners[:5], 1):
            print(f"   {i}. {winner['ticker']}: {winner['roi']:+.1f}% (${winner['entry']:.6f} → ${winner['price']:.6f})")

if __name__ == "__main__":
    main()