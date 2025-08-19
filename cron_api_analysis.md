# API Usage Analysis for Active Cron Jobs

## Active Cron Jobs (Running Every Minute)

### 1. crypto-ath-verifier-every-minute
- **Schedule**: Every minute (1,440 times/day)
- **Function**: Verifies All-Time High prices
- **API Used**: GeckoTerminal OHLCV data
- **Calls per run**: 20-25 tokens processed
- **API calls**: ~25 GeckoTerminal calls per minute
- **Daily total**: **~36,000 GeckoTerminal API calls/day**

### 2. crypto-orchestrator-every-minute  
- **Schedule**: Every minute (1,440 times/day)
- **Function**: Main KROM monitoring pipeline
- **APIs Used**:
  - KROM API (check for new calls)
  - OpenRouter/Claude API (for analysis)
  - ScraperAPI (for X/Twitter analysis)
  - Telegram Bot API (for notifications)
- **Estimated calls per run**: 
  - 1 KROM API call
  - 0-2 OpenRouter calls (when new calls found)
  - 0-10 ScraperAPI calls (when analyzing X)
- **Daily total**: 
  - **1,440 KROM API calls/day**
  - **~100 OpenRouter API calls/day**
  - **~500 ScraperAPI calls/day**
  - **~50 Telegram API calls/day**

### 3. crypto-ultra-tracker-every-minute
- **Schedule**: Every minute (1,440 times/day)
- **Function**: ATH tracking for active tokens
- **API Used**: GeckoTerminal OHLCV data
- **Calls per run**: 30 tokens (batchSize parameter)
- **API calls**: 30 GeckoTerminal calls per minute
- **Daily total**: **~43,200 GeckoTerminal API calls/day**

### 4. krom-call-analysis-every-minute
- **Schedule**: Every minute (1,440 times/day)
- **Function**: Analyzes KROM calls with Kimi K2
- **API Used**: OpenRouter (Kimi K2 model)
- **Calls per run**: 0-5 (processes unanalyzed calls)
- **Daily total**: **~200 OpenRouter API calls/day**

### 5. krom-x-analysis-every-minute
- **Schedule**: Every minute (1,440 times/day)
- **Function**: X/Twitter analysis for KROM calls
- **API Used**: OpenRouter (for analysis)
- **Calls per run**: 0-5 (processes unanalyzed calls)
- **Daily total**: **~200 OpenRouter API calls/day**

### 6. test-cron-now
- **Schedule**: Every minute (1,440 times/day)
- **Function**: Test cron (SELECT 1)
- **API Used**: None
- **Daily total**: **0 API calls**

## TOTAL API USAGE PER DAY

### GeckoTerminal/CoinGecko APIs:
- crypto-ath-verifier: ~36,000 calls/day
- crypto-ultra-tracker: ~43,200 calls/day
- **TOTAL: ~79,200 GeckoTerminal API calls/day**

### OpenRouter (AI) APIs:
- crypto-orchestrator: ~100 calls/day
- krom-call-analysis: ~200 calls/day
- krom-x-analysis: ~200 calls/day
- **TOTAL: ~500 OpenRouter API calls/day**

### Other APIs:
- KROM API: ~1,440 calls/day
- ScraperAPI: ~500 calls/day
- Telegram API: ~50 calls/day

## SUMMARY

**The main API usage culprits are:**
1. **crypto-ultra-tracker**: 43,200 GeckoTerminal calls/day
2. **crypto-ath-verifier**: 36,000 GeckoTerminal calls/day

These two functions alone are making **79,200 GeckoTerminal API calls per day**, which explains the 80% usage warning from CoinGecko.

## RECOMMENDATIONS (Without Disabling)

To reduce API usage without stopping the functions:
1. Reduce frequency of ATH checks (maybe every 5 minutes instead of every minute)
2. Reduce batch sizes (process fewer tokens per run)
3. Implement smarter token selection (only check high-value tokens frequently)