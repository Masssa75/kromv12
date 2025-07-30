#!/usr/bin/env python3
"""
Process ALL remaining tokens with current prices
Optimized for large batch processing with progress updates every 250 tokens
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

def get_remaining_count():
    """Get count of tokens still needing prices"""
    query = f"{SUPABASE_URL}/rest/v1/crypto_calls?select=count&contract_address=not.is.null&network=not.is.null&price_at_call=gt.0&current_price=is.null&price_updated_at=is.null"
    
    resp = requests.get(query, headers=headers)
    if resp.status_code == 200:
        result = resp.json()
        if result and len(result) > 0:
            return result[0].get('count', 0)
    return 0

def get_tokens_batch(limit=100):
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
            time.sleep(1)
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
        
        if price and price > 0:
            roi = ((price - token['price_at_call']) / token['price_at_call'] * 100) if token['price_at_call'] > 0 else 0
            
            if roi > 100:  # Track big winners (>100% ROI)
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
        
        time.sleep(0.15)  # Slightly faster rate limiting
    
    return batch_successful, batch_failed, batch_winners

def main():
    # Get initial count
    remaining = get_remaining_count()
    print(f"🚀 Starting to process ALL remaining tokens")
    print(f"📊 Tokens to process: {remaining:,}")
    print("=" * 60)
    
    total_processed = 0
    total_successful = 0
    total_failed = 0
    all_winners = []
    start_time = time.time()
    
    try:
        while True:
            # Get next batch (100 tokens at a time)
            tokens = get_tokens_batch(100)
            
            if not tokens:
                print(f"\n✅ All tokens processed! Total: {total_processed:,}")
                break
            
            # Process this batch
            batch_successful, batch_failed, batch_winners = process_batch(tokens)
            
            # Update totals
            total_processed += len(tokens)
            total_successful += batch_successful
            total_failed += batch_failed
            all_winners.extend(batch_winners)
            
            # Progress report every 250 tokens
            if total_processed % 250 == 0:
                elapsed_time = time.time() - start_time
                success_rate = (total_successful / total_processed) * 100
                tokens_per_min = (total_processed / elapsed_time) * 60
                eta_minutes = ((remaining - total_processed) / tokens_per_min) if tokens_per_min > 0 else 0
                
                print(f"\n📊 PROGRESS UPDATE - {total_processed:,}/{remaining:,} tokens ({total_processed/remaining*100:.1f}%)")
                print(f"   ⏱️  Time elapsed: {elapsed_time/60:.1f} minutes")
                print(f"   ✅ Successful: {total_successful:,} ({success_rate:.1f}%)")
                print(f"   ❌ Failed: {total_failed:,}")
                print(f"   🏆 Big winners (>100% ROI): {len(all_winners)}")
                print(f"   ⚡ Rate: {tokens_per_min:.1f} tokens/minute")
                print(f"   ⏳ ETA: {eta_minutes:.1f} minutes remaining")
                
                # Show recent big winners
                recent_winners = [w for w in batch_winners if w['roi'] > 100]
                if recent_winners:
                    print(f"   🎉 Recent big winners:")
                    for winner in recent_winners[:3]:
                        print(f"      • {winner['ticker']}: {winner['roi']:+.1f}%")
    
    except KeyboardInterrupt:
        print(f"\n\n👋 Stopped by user at {total_processed:,} tokens")
    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        print(f"   Processed {total_processed:,} tokens before error")
    
    # Final summary
    elapsed_time = time.time() - start_time
    success_rate = (total_successful / total_processed) * 100 if total_processed > 0 else 0
    tokens_per_min = (total_processed / elapsed_time) * 60 if elapsed_time > 0 else 0
    
    print(f"\n📋 FINAL SUMMARY:")
    print(f"   Total processed: {total_processed:,}")
    print(f"   Time taken: {elapsed_time/60:.1f} minutes ({elapsed_time/3600:.1f} hours)")
    print(f"   Successful: {total_successful:,} ({success_rate:.1f}%)")
    print(f"   Failed: {total_failed:,}")
    print(f"   Big winners (>100% ROI): {len(all_winners)}")
    print(f"   Average rate: {tokens_per_min:.1f} tokens/minute")
    
    if all_winners:
        print(f"\n🏆 TOP 20 PERFORMERS:")
        all_winners.sort(key=lambda x: x['roi'], reverse=True)
        for i, winner in enumerate(all_winners[:20], 1):
            print(f"   {i:2d}. {winner['ticker']}: {winner['roi']:+,.1f}% (${winner['entry']:.8f} → ${winner['price']:.8f})")

if __name__ == "__main__":
    main()