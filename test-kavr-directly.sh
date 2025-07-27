#!/bin/bash

echo "Testing KAVR directly with GeckoTerminal API..."

# Test KAVR on GeckoTerminal
echo -e "\n1. Checking if KAVR exists on GeckoTerminal:"
curl -s "https://api.geckoterminal.com/api/v2/networks/eth/tokens/0x5832f53d147b3d6cd4578b9cbd62425c7ea9d0bd" | jq '.data.attributes | {name, symbol, price_usd, fdv_usd, market_cap_usd}'

echo -e "\n2. Checking for KAVR pools:"
curl -s "https://api.geckoterminal.com/api/v2/networks/eth/tokens/0x5832f53d147b3d6cd4578b9cbd62425c7ea9d0bd/pools" | jq '.data | length'

echo -e "\n3. Testing with DexScreener API as alternative:"
curl -s "https://api.dexscreener.com/latest/dex/tokens/0x5832f53d147b3d6cd4578b9cbd62425c7ea9d0bd" | jq '.pairs[0] | {baseToken, priceUsd, priceNative, liquidity}'

echo -e "\n4. Checking CoinGecko (by contract):"
curl -s "https://api.coingecko.com/api/v3/simple/token_price/ethereum?contract_addresses=0x5832f53d147b3d6cd4578b9cbd62425c7ea9d0bd&vs_currencies=usd" | jq '.'