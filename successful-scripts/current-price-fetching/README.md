# Current Price Fetching Scripts

Scripts for fetching current prices of crypto tokens and storing them in the Supabase database.

## Key Scripts

### Main Batch Processors
- **`fetch-current-prices-batch.py`** - Main batch processor using GeckoTerminal API
- **`fetch-current-prices-dexscreener.py`** - DexScreener API version (no rate limits)
- **`fetch-current-prices-dexscreener-fixed.py`** - Enhanced version with better exclusion logic

### Testing & Validation
- **`test-current-price-edge-function.py`** - Tests the Supabase edge function
- **`test-dexscreener-api.py`** - Tests DexScreener API directly
- **`test-ethereum-tokens-fixed.py`** - Validates network mapping fix

### Monitoring
- **`check-current-price-progress.py`** - Monitors how many tokens have current prices

## Critical Network Mapping Fix

**IMPORTANT**: KROM stores network as `"ethereum"` but GeckoTerminal API requires `"eth"`

```python
network_map = {
    'ethereum': 'eth',    # Critical mapping!
    'solana': 'solana',
    'bsc': 'bsc', 
    'polygon': 'polygon',
    'arbitrum': 'arbitrum',
    'base': 'base'
}
mapped_network = network_map.get(network, network)
```

**Impact**: Success rate improved from 52% to 84% after implementing this fix.

## Database Schema

Scripts update these columns in the `crypto_calls` table:
- `current_price` - Current token price
- `price_updated_at` - Timestamp of price update
- `roi_percent` - ROI calculation: `((current_price - price_at_call) / price_at_call) * 100`

## API Sources

### DexScreener (Recommended)
- **Endpoint**: `https://api.dexscreener.com/latest/dex/tokens/{address}`
- **Rate Limits**: None documented
- **Authentication**: Not required
- **Coverage**: Excellent for popular tokens

### GeckoTerminal (Fallback)
- **Endpoint**: `https://api.geckoterminal.com/api/v2/networks/{network}/tokens/{address}/pools`
- **Rate Limits**: Aggressive (requires delays)
- **Authentication**: Not required
- **Network Mapping**: Required (see above)

## Session Context (July 28, 2025)

### Problems Solved
1. **UI Display Issue**: Fixed PriceDisplay component showing market caps instead of actual prices
2. **Network Mapping**: Fixed Ethereum token failures by mapping 'ethereum' → 'eth'
3. **Dead Token Detection**: Identified tokens that were delisted after initial calls
4. **Clear-Prices Bug**: Discovered API clears prices but not timestamps (5,701 affected records)

### Key Findings
- Many old tokens show 80-96% losses (expected for meme coins)
- DexScreener API more reliable than GeckoTerminal for batch processing
- BIP177 exists multiple times in database (not a bug - separate calls)
- Success rate: ~84% after network mapping fix

### Next Steps
1. Fix clear-prices API to also clear `price_updated_at` timestamps
2. Continue batch processing remaining ~5,500 tokens
3. Implement UI auto-refresh for stale prices (>6 hours old)
4. Set up cron job for continuous price updates