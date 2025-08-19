#!/usr/bin/env python3
"""
Test CoinAPI.io capabilities for token discovery
"""
import requests
import json
from datetime import datetime, timedelta

# API configuration
API_KEY = "f1f0d492-1c7a-4473-a78f-4fe3bfb742ed"
BASE_URL = "https://rest.coinapi.io/v1"
HEADERS = {"X-CoinAPI-Key": API_KEY}

def test_assets_endpoint():
    """Test the assets endpoint to see what data is available"""
    print("\n=== Testing Assets Endpoint ===")
    
    # Get all crypto assets
    url = f"{BASE_URL}/assets?filter_type_is_crypto=1"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        assets = response.json()
        print(f"Total crypto assets: {len(assets)}")
        
        # Show first 5 assets with all fields
        print("\nFirst 5 assets with all fields:")
        for asset in assets[:5]:
            print(f"\n{asset.get('asset_id')} - {asset.get('name')}")
            print(json.dumps(asset, indent=2))
            
        # Check if any have website/social data
        print("\n=== Checking for website/social media fields ===")
        sample = assets[0] if assets else {}
        fields = list(sample.keys()) if sample else []
        print(f"Available fields: {fields}")
        
        # Look for recent assets (by data_trade_start)
        recent_assets = [a for a in assets if a.get('data_trade_start')]
        recent_assets.sort(key=lambda x: x.get('data_trade_start', ''), reverse=True)
        
        print(f"\n=== 10 Most Recently Added Assets (by trade data) ===")
        for asset in recent_assets[:10]:
            print(f"{asset.get('data_trade_start', 'N/A')}: {asset.get('asset_id')} - {asset.get('name')}")
            
    else:
        print(f"Error: {response.status_code} - {response.text}")
    
    return response.headers

def test_symbols_endpoint():
    """Test the symbols endpoint for new listings"""
    print("\n=== Testing Symbols Endpoint ===")
    
    # Get all symbols
    url = f"{BASE_URL}/symbols"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        symbols = response.json()
        print(f"Total symbols: {len(symbols)}")
        
        # Filter for spot symbols (not derivatives)
        spot_symbols = [s for s in symbols if s.get('symbol_type') == 'SPOT']
        print(f"Spot symbols: {len(spot_symbols)}")
        
        # Show first symbol with all fields
        if symbols:
            print("\nFirst symbol with all fields:")
            print(json.dumps(symbols[0], indent=2))
            
        # Look for recent symbols
        recent_symbols = [s for s in symbols if s.get('data_start')]
        recent_symbols.sort(key=lambda x: x.get('data_start', ''), reverse=True)
        
        print(f"\n=== 10 Most Recently Added Symbols ===")
        for symbol in recent_symbols[:10]:
            print(f"{symbol.get('data_start', 'N/A')}: {symbol.get('symbol_id')} on {symbol.get('exchange_id')}")
            
        # Check specific exchanges
        print("\n=== Exchange Coverage ===")
        exchanges = set(s.get('exchange_id') for s in symbols if s.get('exchange_id'))
        print(f"Total exchanges: {len(exchanges)}")
        
        # Look for DEX exchanges
        dex_exchanges = [e for e in exchanges if any(dex in e.lower() for dex in ['uniswap', 'pancake', 'sushi', 'raydium'])]
        print(f"DEX exchanges found: {dex_exchanges[:10]}")
        
    else:
        print(f"Error: {response.status_code} - {response.text}")

def test_exchanges_endpoint():
    """Test exchanges endpoint to see coverage"""
    print("\n=== Testing Exchanges Endpoint ===")
    
    url = f"{BASE_URL}/exchanges"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        exchanges = response.json()
        print(f"Total exchanges: {len(exchanges)}")
        
        # Look for DEXs
        dexs = [e for e in exchanges if any(dex in e.get('name', '').lower() or dex in e.get('exchange_id', '').lower() 
                                             for dex in ['uniswap', 'pancake', 'sushi', 'raydium', 'jupiter', '1inch'])]
        
        print("\n=== DEX Coverage ===")
        for dex in dexs:
            print(f"- {dex.get('exchange_id')}: {dex.get('name')} (Website: {dex.get('website', 'N/A')})")
            
    else:
        print(f"Error: {response.status_code} - {response.text}")

def check_rate_limits(headers):
    """Check rate limit headers"""
    print("\n=== Rate Limit Information ===")
    for key, value in headers.items():
        if 'limit' in key.lower() or 'remaining' in key.lower() or 'quota' in key.lower():
            print(f"{key}: {value}")

if __name__ == "__main__":
    print("Testing CoinAPI.io for Token Discovery Capabilities")
    print("=" * 60)
    
    # Test different endpoints
    headers = test_assets_endpoint()
    check_rate_limits(headers)
    
    test_symbols_endpoint()
    test_exchanges_endpoint()
    
    print("\n" + "=" * 60)
    print("Test Complete!")