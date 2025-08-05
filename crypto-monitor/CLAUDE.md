# Crypto Monitor & Notifier Documentation

## Overview
This is the original KROM cryptocurrency monitoring system that runs entirely on Supabase Edge Functions. It polls the KROM API for new crypto calls, analyzes them with AI, performs X (Twitter) research, and sends notifications to Telegram.

## Architecture Flow
```
Cron Job (every minute) → crypto-orchestrator
                              ↓
                         crypto-poller (fetches new calls)
                              ↓
                    Parallel execution:
                    ├─ crypto-analyzer (Claude analysis)
                    └─ crypto-x-analyzer-nitter (X research)
                              ↓
                         crypto-notifier (Telegram notifications)
```

## Edge Functions

### 1. crypto-orchestrator
- **Purpose**: Main coordinator that runs all functions in sequence
- **File**: `/edge-functions/crypto-orchestrator-with-x.ts`
- **Timing**: ~5-20 seconds total execution

### 2. crypto-poller
- **Purpose**: Fetches new calls from KROM API
- **File**: `/edge-functions/crypto-poller.ts`
- **Optimizations**: 
  - Only fetches 10 calls from API (`?limit=10`)
  - Only processes first 5 calls

### 3. crypto-analyzer
- **Purpose**: Analyzes calls using Claude API
- **File**: `/edge-functions/crypto-analyzer.ts`
- **Processes**: 10 calls at a time
- **Model**: claude-3-haiku-20240307

### 4. crypto-x-analyzer-nitter
- **Purpose**: Fetches X/Twitter data and analyzes with Claude
- **File**: `/edge-functions/crypto-x-analyzer-nitter.ts`
- **Method**: ScraperAPI + Nitter (free alternative to X API)
- **Processes**: 5 calls at a time

### 5. crypto-notifier
- **Purpose**: Sends Telegram notifications to dual bots
- **File**: `/edge-functions/crypto-notifier-complete.ts`
- **Features**:
  - **Dual Bot Support**: Regular bot (all calls) + Premium bot (SOLID/ALPHA only)
  - Shows both analysis tiers
  - Uses better tier for header and filtering
  - Includes X summary
  - Limits to 10 notifications per run per bot
  - Separate tracking via `notified` and `notified_premium` columns

## Environment Variables (Secrets)
Required in Supabase Edge Functions:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_ANON_KEY`
- `KROM_API_TOKEN`
- `ANTHROPIC_API_KEY`
- `SCRAPERAPI_KEY`
- `TELEGRAM_BOT_TOKEN` - Regular bot (all notifications)
- `TELEGRAM_GROUP_ID` - Regular group chat ID
- `TELEGRAM_BOT_TOKEN_PREMIUM` - Premium bot (SOLID/ALPHA only)
- `TELEGRAM_GROUP_ID_PREMIUM` - Premium group chat ID (-1002511942743)

## External Services

### 1. KROM API
- **Endpoint**: `https://krom.one/api/v1/calls`
- **Auth**: Bearer token
- **Limit**: Request only 10 calls with `?limit=10`

### 2. Claude API (Anthropic)
- **Endpoint**: `https://api.anthropic.com/v1/messages`
- **Model**: claude-3-haiku-20240307
- **Cost**: ~$0.25 per 1M input tokens

### 3. ScraperAPI
- **Endpoint**: `https://api.scraperapi.com/`
- **Purpose**: Fetch Nitter pages
- **Limit**: 1000 requests/month (free tier)

### 4. Nitter
- **URL**: `https://nitter.net/search?q=CONTRACT_ADDRESS&f=tweets`
- **Purpose**: Free Twitter mirror
- **No API needed**

### 5. Telegram Bot API
- **Endpoint**: `https://api.telegram.org/bot{TOKEN}/sendMessage`
- **Parse Mode**: Markdown
- **Dual Bot Setup**:
  - Regular Bot: KROMinstant (all calls) → Main group
  - Premium Bot: KROMinstantALPHA (@KROMinstantALPHA_bot) → "EXTREME CALLS!!" group

### 6. Cron-job.org
- **Frequency**: Every 1 minute
- **Target**: crypto-orchestrator Edge Function
- **Timeout**: Set to maximum (30 seconds)

## Current State & Optimizations

### Performance
- Total execution: 5-20 seconds
- Poller: ~2-4 seconds
- Analysis: ~3-10 seconds (parallel)
- Notifier: ~2-4 seconds

### Limits
- Claude: 10 calls per run
- X Research: 5 calls per run
- Notifications: 10 per run
- ScraperAPI: 1000 requests/month

### Recent Fixes
1. X API too expensive → Switched to ScraperAPI + Nitter
2. Notification spam → Added 10 notification limit
3. Slow polling → Limited to 5 most recent calls
4. Network blocks → Used ScraperAPI proxy

## Testing

### Manual Testing
```bash
# Test individual functions
supabase functions invoke crypto-poller
supabase functions invoke crypto-analyzer
supabase functions invoke crypto-x-analyzer-nitter
supabase functions invoke crypto-notifier

# Test full pipeline
supabase functions invoke crypto-orchestrator
```

### Check Logs
- Supabase Dashboard → Edge Functions → View Logs

## Notification Format
```
💎 NEW ALPHA CALL: BTC on Crypto Signals

📊 Analysis Ratings:
• Call Quality: ALPHA | X Research: SOLID

📝 Original Message:
"Big news coming for BTC! 🚀"

🐦 X Summary:
• Major exchange listing confirmed
• Partnership with Fortune 500 company
• Active development team

📊 Token: BTC
🏷️ Group: Crypto Signals
[... more details ...]
```

## Common Issues & Solutions

1. **No notifications sent**
   - Check if calls are analyzed (`analyzed_at` not null)
   - Check if X analysis completed (`x_analyzed_at` not null)
   - Verify Telegram credentials

2. **Slow performance**
   - Reduce number of calls processed
   - Check API rate limits
   - Monitor Edge Function timeouts

3. **X analysis failing**
   - Verify ScraperAPI key
   - Check if Nitter instance is up
   - Review HTML parsing patterns

## Known Issues & Notes
- X analyzer currently rates most calls as TRASH (expected - only 1-2 SOLID/ALPHA per week)
- Premium bot will be significantly quieter than regular bot (SOLID/ALPHA calls only)
- System is optimized for ~1-5 calls per minute normal operation
- All functions work correctly as of last testing
- Dual bot notification system fully operational

---
**Last Updated**: August 5, 2025