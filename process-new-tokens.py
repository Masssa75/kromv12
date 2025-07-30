#!/usr/bin/env python3
"""
Process new tokens that just came in
"""
import os
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

NETWORK_MAP = {
    'ethereum': 'eth',
    'solana': 'solana', 
    'bsc': 'bsc',
    'polygon': 'polygon',
    'arbitrum': 'arbitrum',
    'base': 'base'
}

def get_new_tokens():
    """Get new tokens that need price updates"""
    query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id,ticker,contract_address,network,price_at_call,created_at&current_price=is.null&price_at_call=not.is.null&contract_address=not.is.null&order=created_at.desc&limit=100"
    
    resp = requests.get(query, headers=headers)
    if resp.status_code != 200:
        print(f"❌ Query failed: {resp.status_code}")
        return []
    
    return resp.json()

def fetch_price_dexscreener(contract_address):
    """Try to fetch price from DexScreener"""
    try:
        resp = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}", timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            if data.get('pairs') and len(data['pairs']) > 0:
                price = float(data['pairs'][0]['priceUsd'])
                return price, "DexScreener"
    except:
        pass
    return None, None

def fetch_price_geckoterminal(contract_address, network):
    """Try to fetch price from GeckoTerminal"""
    try:
        api_network = NETWORK_MAP.get(network, network)
        resp = requests.get(f"https://api.geckoterminal.com/api/v2/networks/{api_network}/tokens/{contract_address}/pools", timeout=5)
        
        if resp.status_code == 429:
            time.sleep(2)
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
    except:
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
    print("🚀 Processing New Tokens")
    print("=" * 50)
    
    tokens = get_new_tokens()
    if not tokens:
        print("✅ No new tokens found!")
        return
    
    print(f"📊 Found {len(tokens)} new tokens to process\n")
    
    successful = 0
    failed = 0
    winners = []
    
    for i, token in enumerate(tokens, 1):
        created_time = datetime.fromisoformat(token['created_at'].replace('Z', '+00:00'))
        age_minutes = (datetime.now(timezone.utc) - created_time).total_seconds() / 60
        
        print(f"[{i}/{len(tokens)}] 📊 {token['ticker']} ({token['network']}) - {age_minutes:.0f} mins old")
        print(f"    CA: {token['contract_address'][:20]}...")
        print(f"    Entry: ${token['price_at_call']:.8f}", end="", flush=True)
        
        # Try DexScreener first
        price, source = fetch_price_dexscreener(token['contract_address'])
        
        # If DexScreener fails, try GeckoTerminal
        if price is None:
            price, source = fetch_price_geckoterminal(token['contract_address'], token['network'])
        
        if price and price > 0:
            roi = ((price - token['price_at_call']) / token['price_at_call'] * 100)
            roi_symbol = "📈" if roi > 0 else "📉"
            
            if roi > 0:
                winners.append({
                    'ticker': token['ticker'], 
                    'roi': roi,
                    'age_mins': age_minutes
                })
            
            if update_token_price(token['id'], price):
                successful += 1
                print(f" → ${price:.8f} ({source}) {roi_symbol} {roi:+.1f}% ✅")
            else:
                failed += 1
                print(f" → DB update failed ❌")
        else:
            failed += 1
            print(f" → No price found ❌")
        
        time.sleep(0.3)
    
    print(f"\n📋 SUMMARY:")
    print(f"   Successful: {successful}/{len(tokens)} ({successful/len(tokens)*100:.1f}%)")
    print(f"   Failed: {failed}/{len(tokens)}")
    print(f"   Winners: {len(winners)}")
    
    if winners:
        print(f"\n🎉 Winners:")
        winners.sort(key=lambda x: x['roi'], reverse=True)
        for winner in winners:
            print(f"   • {winner['ticker']}: {winner['roi']:+.1f}% ({winner['age_mins']:.0f} mins old)")

if __name__ == "__main__":
    main()