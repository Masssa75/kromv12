#!/usr/bin/env python3
"""
Process 1000 tokens with current prices - hourly batch processor
Updates every 100 tokens processed
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

def get_tokens_batch(limit=50):
    """Get next batch of tokens that need price updates"""
    query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=id,ticker,contract_address,network,price_at_call&contract_address=not.is.null&network=not.is.null&price_at_call=gt.0&current_price=is.null&price_updated_at=is.null&order=id.asc&limit={limit}"
    
    resp = requests.get(query, headers=headers)
    if resp.status_code != 200:
        print(f"❌ Query failed: {resp.status_code}")
        return []
    
    return resp.json()

def fetch_price_dexscreener(contract_address):
    """Try to fetch price from DexScreener"""
    try:
        resp = requests.get(f"https://api.dexscreener.com/latest/dex/tokens/{contract_address}")
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
        resp = requests.get(f"https://api.geckoterminal.com/api/v2/networks/{api_network}/tokens/{contract_address}/pools")
        
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

def process_batch(batch_tokens):
    """Process a batch of tokens"""
    batch_successful = 0
    batch_failed = 0
    batch_winners = []
    
    for token in batch_tokens:
        # Try DexScreener first
        price, source = fetch_price_dexscreener(token['contract_address'])
        
        # If DexScreener fails, try GeckoTerminal
        if price is None:
            price, source = fetch_price_geckoterminal(token['contract_address'], token['network'])
        
        if price:
            roi = ((price - token['price_at_call']) / token['price_at_call'] * 100)
            
            if roi > 0:
                batch_winners.append({
                    'ticker': token['ticker'], 
                    'roi': roi,
                    'price': price,
                    'entry': token['price_at_call']
                })
            
            if update_token_price(token['id'], price):
                batch_successful += 1
            else:
                batch_failed += 1
        else:
            batch_failed += 1
        
        time.sleep(0.2)  # Rate limiting
    
    return batch_successful, batch_failed, batch_winners

def main():
    print("🚀 Starting 1000 Token Batch Processing")
    print("=" * 60)
    
    TARGET_COUNT = 1000
    total_processed = 0
    total_successful = 0
    total_failed = 0
    all_winners = []
    start_time = time.time()
    
    try:
        while total_processed < TARGET_COUNT:
            # Get next batch
            batch_size = min(50, TARGET_COUNT - total_processed)
            tokens = get_tokens_batch(batch_size)
            
            if not tokens:
                print(f"\n✅ No more tokens found! Processed {total_processed} total.")
                break
            
            print(f"\n🔄 Processing batch: tokens {total_processed + 1}-{total_processed + len(tokens)}")
            
            # Process this batch
            batch_successful, batch_failed, batch_winners = process_batch(tokens)
            
            # Update totals
            total_processed += len(tokens)
            total_successful += batch_successful
            total_failed += batch_failed
            all_winners.extend(batch_winners)
            
            # Progress report every 100 tokens
            if total_processed % 100 == 0 or total_processed >= TARGET_COUNT:
                elapsed_time = time.time() - start_time
                success_rate = (total_successful / total_processed) * 100
                tokens_per_min = (total_processed / elapsed_time) * 60
                
                print(f"\n📊 PROGRESS UPDATE - {total_processed}/{TARGET_COUNT} tokens")
                print(f"   ⏱️  Time elapsed: {elapsed_time/60:.1f} minutes")
                print(f"   ✅ Successful: {total_successful} ({success_rate:.1f}%)")
                print(f"   ❌ Failed: {total_failed}")
                print(f"   🏆 Winners: {len(all_winners)}")
                print(f"   ⚡ Rate: {tokens_per_min:.1f} tokens/minute")
                
                # Show recent winners
                if batch_winners:
                    print(f"   🎉 New winners in this batch:")
                    for winner in batch_winners[-3:]:  # Show last 3 winners
                        print(f"      • {winner['ticker']}: {winner['roi']:+.1f}%")
    
    except KeyboardInterrupt:
        print(f"\n\n👋 Stopped by user at {total_processed} tokens")
    
    # Final summary
    elapsed_time = time.time() - start_time
    success_rate = (total_successful / total_processed) * 100 if total_processed > 0 else 0
    tokens_per_min = (total_processed / elapsed_time) * 60 if elapsed_time > 0 else 0
    
    print(f"\n📋 FINAL SUMMARY:")
    print(f"   Total processed: {total_processed}/{TARGET_COUNT}")
    print(f"   Time taken: {elapsed_time/60:.1f} minutes")
    print(f"   Successful: {total_successful} ({success_rate:.1f}%)")
    print(f"   Failed: {total_failed}")
    print(f"   Winners: {len(all_winners)}")
    print(f"   Average rate: {tokens_per_min:.1f} tokens/minute")
    
    if all_winners:
        print(f"\n🏆 TOP 10 PERFORMERS:")
        all_winners.sort(key=lambda x: x['roi'], reverse=True)
        for i, winner in enumerate(all_winners[:10], 1):
            print(f"   {i:2d}. {winner['ticker']}: {winner['roi']:+.1f}% (${winner['entry']:.6f} → ${winner['price']:.6f})")

if __name__ == "__main__":
    main()