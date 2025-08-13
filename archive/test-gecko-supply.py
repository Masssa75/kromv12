#!/usr/bin/env python3
"""
Test GeckoTerminal API to verify supply data fields
"""

import requests

# Test with a known Solana pool
pool_address = "8pgeS9KbfUwBaWXfPH6aSrCLDEUZhFQNvGqFCD2Epump"
network = "solana"

url = f"https://api.geckoterminal.com/api/v2/networks/{network}/pools/{pool_address}"

print("Testing GeckoTerminal API for supply data...")
print(f"URL: {url}\n")

response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})

if response.status_code == 200:
    data = response.json()
    attributes = data['data']['attributes']
    
    print("Key fields from GeckoTerminal:")
    print(f"  Token name: {attributes.get('name')}")
    print(f"  Price USD: ${attributes.get('base_token_price_usd')}")
    print(f"  FDV USD: ${attributes.get('fdv_usd'):,.0f}" if attributes.get('fdv_usd') else "  FDV USD: None")
    print(f"  Market Cap USD: ${attributes.get('market_cap_usd'):,.0f}" if attributes.get('market_cap_usd') else "  Market Cap USD: None")
    
    # Calculate supplies
    price = float(attributes.get('base_token_price_usd', 0))
    fdv = float(attributes.get('fdv_usd', 0))
    market_cap = float(attributes.get('market_cap_usd', 0))
    
    if price > 0:
        if fdv > 0:
            total_supply = fdv / price
            print(f"\nCalculated Total Supply: {total_supply:,.0f}")
        
        if market_cap > 0:
            circ_supply = market_cap / price
            print(f"Calculated Circulating Supply: {circ_supply:,.0f}")
            
        if fdv > 0 and market_cap > 0:
            diff_percent = abs(market_cap - fdv) / fdv * 100
            print(f"\nSupply difference: {diff_percent:.1f}%")
            if diff_percent < 5:
                print("✅ Supplies are similar - can calculate historical market caps")
            else:
                print("⚠️ Supplies differ significantly - skip historical market caps")
else:
    print(f"Error: {response.status_code}")