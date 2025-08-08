#!/usr/bin/env python3
"""
Process Dead Tokens - PARALLEL VERSION
=======================================
Uses GeckoTerminal API with parallel processing (100-200 req/min)
Checks dead tokens and revives them if trading again
"""

import os
import time
import warnings
warnings.filterwarnings("ignore")
import requests
from datetime import datetime
from dotenv import load_dotenv
from supabase import create_client
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Semaphore
import threading

load_dotenv()

# Initialize Supabase
supabase = create_client(
    os.getenv('SUPABASE_URL'),
    os.getenv('SUPABASE_SERVICE_ROLE_KEY')
)

# Rate limiting - 150 requests per minute (conservative for paid API)
REQUESTS_PER_MINUTE = 150
RATE_LIMIT_SEMAPHORE = Semaphore(REQUESTS_PER_MINUTE)
PARALLEL_WORKERS = 20  # Number of parallel threads

# Thread-safe counters
stats_lock = threading.Lock()
stats = {
    'updated': 0,  # Tokens with supply/market cap data added
    'no_data': 0,  # Tokens with no GeckoTerminal data
    'errors': 0,
    'processed': 0
}

# GeckoTerminal network mapping
NETWORK_MAP = {
    'ethereum': 'eth',
    'solana': 'solana',
    'bsc': 'bsc',
    'polygon': 'polygon',
    'arbitrum': 'arbitrum',
    'base': 'base',
    'optimism': 'optimism',
    'avalanche': 'avalanche'
}

def rate_limited_request(func):
    """Decorator to rate limit API requests"""
    def wrapper(*args, **kwargs):
        RATE_LIMIT_SEMAPHORE.acquire()
        # Schedule release after 60 seconds
        threading.Timer(60.0, RATE_LIMIT_SEMAPHORE.release).start()
        return func(*args, **kwargs)
    return wrapper

@rate_limited_request
def fetch_token_from_geckoterminal(network, pool_address, contract_address=None):
    """Fetch token data from GeckoTerminal API (rate limited) - tries pool first, then contract"""
    gecko_network = NETWORK_MAP.get(network.lower())
    if not gecko_network:
        return None
    
    # Try pool address first
    url = f"https://api.geckoterminal.com/api/v2/networks/{gecko_network}/pools/{pool_address}"
    
    try:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        
        # If pool fails and we have contract address, try that
        if response.status_code == 404 and contract_address:
            # Try fetching by token contract address instead
            url = f"https://api.geckoterminal.com/api/v2/networks/{gecko_network}/tokens/{contract_address}"
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
            
            if response.status_code == 200:
                # Get the token's top pool
                data = response.json()
                token_attrs = data.get('data', {}).get('attributes', {})
                
                # Get the top pool for this token
                pools_url = f"https://api.geckoterminal.com/api/v2/networks/{gecko_network}/tokens/{contract_address}/pools"
                pools_response = requests.get(pools_url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
                
                if pools_response.status_code == 200:
                    pools_data = pools_response.json()
                    if pools_data.get('data'):
                        # Use the first (top) pool
                        pool_data = pools_data['data'][0]
                        attributes = pool_data.get('attributes', {})
                        
                        # Process pool data below
                        response = pools_response
                        data = {'data': pool_data}
        
        if response.status_code == 200:
            data = response.json()
            attributes = data.get('data', {}).get('attributes', {})
            
            if attributes and attributes.get('base_token_price_usd'):
                price = float(attributes.get('base_token_price_usd', 0))
                fdv = float(attributes.get('fdv_usd', 0))
                market_cap = float(attributes.get('market_cap_usd') or 0)
                volume_24h = float(attributes.get('volume_usd', {}).get('h24', 0))
                liquidity = float(attributes.get('reserve_in_usd', 0))
                
                # Calculate supplies
                total_supply = None
                circulating_supply = None
                
                if price > 0:
                    if fdv > 0:
                        total_supply = fdv / price
                    if market_cap > 0:
                        circulating_supply = market_cap / price
                    elif total_supply:
                        circulating_supply = total_supply  # Assume fully circulating
                
                return {
                    'is_trading': True,
                    'current_price': price,
                    'fdv': fdv,
                    'market_cap': market_cap,
                    'total_supply': total_supply,
                    'circulating_supply': circulating_supply,
                    'volume_24h': volume_24h,
                    'liquidity_usd': liquidity
                }
        
        return {'is_trading': False}
    
    except Exception as e:
        return None

def process_single_token(token):
    """Process a single token and update database if needed"""
    ticker = token['ticker']
    network = token['network']
    pool_address = token['pool_address']
    contract_address = token.get('contract_address')
    
    # Fetch from GeckoTerminal (tries pool first, then contract as fallback)
    gecko_data = fetch_token_from_geckoterminal(network, pool_address, contract_address)
    
    # Update stats
    with stats_lock:
        stats['processed'] += 1
        current_processed = stats['processed']
    
    # Progress indicator every 50 tokens
    if current_processed % 50 == 0:
        with stats_lock:
            print(f"\nProgress: {stats['processed']}/{total_tokens} tokens")
            print(f"  Updated: {stats['updated']}, No data: {stats['no_data']}, Errors: {stats['errors']}")
    
    if not gecko_data:
        with stats_lock:
            stats['errors'] += 1
        return f"Error: {ticker}"
    
    if gecko_data['is_trading']:
        # Token has data on GeckoTerminal - update supply and market cap ONLY
        # DO NOT change is_dead flag - that's managed by DexScreener availability
        update_data = {
            # Remove is_dead update - keep tokens marked as dead
            'current_price': gecko_data['current_price'],
            'volume_24h': gecko_data['volume_24h'],
            'liquidity_usd': gecko_data['liquidity_usd'],
            'price_updated_at': datetime.utcnow().isoformat()
        }
        
        # Add supply data if we got it
        if gecko_data['total_supply']:
            update_data['total_supply'] = gecko_data['total_supply']
            update_data['supply_updated_at'] = datetime.utcnow().isoformat()
            
            # Calculate market_cap_at_call if we have price_at_call
            if token['price_at_call'] and gecko_data['total_supply']:
                # Check if supplies are similar (within 5%)
                if gecko_data['circulating_supply']:
                    diff = abs(gecko_data['circulating_supply'] - gecko_data['total_supply'])
                    diff_percent = (diff / gecko_data['total_supply'] * 100) if gecko_data['total_supply'] > 0 else 0
                    if diff_percent < 5:
                        update_data['market_cap_at_call'] = float(token['price_at_call']) * gecko_data['total_supply']
        
        if gecko_data['circulating_supply']:
            update_data['circulating_supply'] = gecko_data['circulating_supply']
            # Calculate current market cap
            update_data['current_market_cap'] = gecko_data['current_price'] * gecko_data['circulating_supply']
        
        # Update database
        try:
            supabase.table('crypto_calls').update(update_data).eq('id', token['id']).execute()
            with stats_lock:
                stats['updated'] += 1
            
            result_msg = f"✅ UPDATED: {ticker} ({network}) - "
            result_msg += f"Price: ${gecko_data['current_price']:.8f}, "
            result_msg += f"Vol: ${gecko_data['volume_24h']:,.0f}, "
            result_msg += f"Liq: ${gecko_data['liquidity_usd']:,.0f}"
            
            if gecko_data['total_supply']:
                result_msg += f", Supply: {gecko_data['total_supply']:,.0f}"
            
            return result_msg
                
        except Exception as e:
            with stats_lock:
                stats['errors'] += 1
            return f"❌ DB Error for {ticker}: {e}"
    else:
        # Still dead
        with stats_lock:
            stats['no_data'] += 1
        return None  # Don't print still dead tokens

def process_dead_tokens():
    """Main processing function with parallel execution"""
    global total_tokens
    
    print("=" * 60)
    print("Dead Token Processor - PARALLEL VERSION")
    print(f"Rate Limit: {REQUESTS_PER_MINUTE} requests/minute")
    print(f"Parallel Workers: {PARALLEL_WORKERS}")
    print("=" * 60)
    
    # Get dead tokens with pool addresses
    print("\nFetching dead tokens...")
    result = supabase.table('crypto_calls').select(
        'id,ticker,network,contract_address,pool_address,price_at_call,'
        'total_supply,circulating_supply,is_dead'
    ).eq('is_dead', True).not_.is_('pool_address', 'null').is_('total_supply', 'null').execute()  # Process all remaining dead tokens on retry
    
    dead_tokens = result.data
    total_tokens = len(dead_tokens)
    print(f"Found {total_tokens} dead tokens to check")
    
    if not dead_tokens:
        print("No dead tokens to process")
        return
    
    # Estimate processing time
    batches_needed = (total_tokens + REQUESTS_PER_MINUTE - 1) // REQUESTS_PER_MINUTE
    estimated_time = batches_needed  # minutes
    print(f"\nEstimated processing time: ~{estimated_time} minutes")
    print("(Processing in parallel with rate limiting)")
    
    print("\nStarting parallel processing...")
    print("-" * 60)
    
    start_time = time.time()
    
    # Process tokens in parallel
    with ThreadPoolExecutor(max_workers=PARALLEL_WORKERS) as executor:
        # Submit all tasks
        futures = {executor.submit(process_single_token, token): token for token in dead_tokens}
        
        # Process completed tasks
        for future in as_completed(futures):
            result = future.result()
            if result and result.startswith("✅"):
                print(f"\n{result}")
    
    elapsed_time = time.time() - start_time
    
    # Summary
    print("\n\n" + "=" * 60)
    print("Processing Complete!")
    print("=" * 60)
    print(f"Total time: {elapsed_time/60:.1f} minutes")
    print(f"Tokens checked: {stats['processed']}")
    print(f"Updated with supply/MC data: {stats['updated']} 🎉")
    print(f"No GeckoTerminal data: {stats['no_data']}")
    print(f"Errors: {stats['errors']}")
    print(f"Processing rate: {stats['processed']/(elapsed_time/60):.1f} tokens/minute")
    
    if stats['updated'] > 0:
        print("\n✨ Updated tokens now have:")
        print("  - Current price and volume data")
        print("  - Supply data (total & circulating)")
        print("  - Market cap calculations")
        print("  - Tokens remain marked as 'dead' for DexScreener tracking")
        print("\nMarket caps are now available for analysis and reporting!")
    
    print("=" * 60)

if __name__ == "__main__":
    # Show info about processing
    print("\n🚀 PARALLEL PROCESSING MODE")
    print(f"This will process {PARALLEL_WORKERS} tokens simultaneously")
    print(f"Rate limited to {REQUESTS_PER_MINUTE} requests per minute")
    print("Expected time for 3000 tokens: ~20 minutes")
    
    # Auto-proceed for automated run
    print("\nAuto-proceeding with processing...")
    process_dead_tokens()