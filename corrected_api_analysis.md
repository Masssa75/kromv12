# CORRECTED API Usage Analysis

## API Breakdown by Service

### DexScreener API Usage:
1. **crypto-ultra-tracker**: 43,200 calls/day (30 tokens/minute)
2. **crypto-poller** (in orchestrator): ~100 calls/day (for new KROM calls)
3. **token-website-monitor** (DISABLED): was 864 calls/day
4. **Total DexScreener**: **~43,300 calls/day**

### GeckoTerminal API Usage (This is CoinGecko!):
1. **crypto-ath-verifier**: 36,000 calls/day (uses api.geckoterminal.com)
2. **token-discovery-rapid** (DISABLED): was ~1,440 calls/day
3. **Total GeckoTerminal**: **~36,000 calls/day**

### CoinGecko Pro API Usage:
- **crypto-ath-verifier**: Also has CoinGecko Pro API as backup
- But primarily uses GeckoTerminal

## THE REAL PROBLEM

**GeckoTerminal IS part of CoinGecko!** 
- api.geckoterminal.com is owned by CoinGecko
- This counts against your CoinGecko API limit

So your 80% usage warning is from:
1. **crypto-ath-verifier**: 36,000 GeckoTerminal (CoinGecko) calls/day
2. **token-discovery-rapid** (now disabled): was 1,440 GeckoTerminal calls/day

**Total was: ~37,440 CoinGecko API calls/day**

## Current Status After Disabling Token Discovery:

- **Still running**: crypto-ath-verifier (36,000 CoinGecko calls/day)
- **Not affecting CoinGecko**: crypto-ultra-tracker (uses DexScreener, different service)
- **Not affecting CoinGecko**: Other functions (use different APIs)

## To Further Reduce CoinGecko Usage:

The only remaining high-usage CoinGecko function is **crypto-ath-verifier** making 36,000 calls/day.

Options:
1. Reduce frequency from every minute to every 5 minutes (7,200 calls/day)
2. Reduce batch size from 25 to 10 tokens (14,400 calls/day)
3. Temporarily disable it until next billing cycle
4. Switch it to use DexScreener API instead of GeckoTerminal