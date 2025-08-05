# KROMV12 Active Files
**Last Updated**: August 5, 2025
**Version**: 8.2.0 - Native Cron Migration & System Reliability Improvements

⚠️ **DATABASE NOTICE**: All KROM apps use SUPABASE exclusively. The local SQLite database is LEGACY only.
⚠️ **RLS ENABLED**: Write operations now require SUPABASE_SERVICE_ROLE_KEY (not anon key).

These are the currently active files in the KROMV12 project:

## Krom Analysis App (DEPLOYED ✅)
- **Live URL**: https://lively-torrone-8199e0.netlify.app
- **GitHub**: https://github.com/Masssa75/krom-analysis-app
- **Netlify Site ID**: 8ff019b3-29ef-4223-b6ad-2cc46e91807e

### Key Files in krom-analysis-app/
- `app/page.tsx` - Main UI with date column (Thai timezone), price display, GeckoTerminal panel
- `app/api/analyze/route.ts` - Call analysis API (1-10 scoring)
- `app/api/x-batch/route.ts` - X batch analysis API (processes stored tweets)
- `app/api/analyzed/route.ts` - Fetches analyzed calls with price data
- `app/api/token-price/route.ts` - Single token price fetching
- `app/api/batch-price-fetch/route.ts` - Batch price processing
- `app/api/save-price-data/route.ts` - Saves price data to database
- `app/api/cron/analyze/route.ts` - Automated call analysis endpoint
- `app/api/cron/x-analyze/route.ts` - Automated X analysis endpoint
- `components/price-display.tsx` - Price/ROI display using Supabase edge function
- `components/geckoterminal-panel.tsx` - Enhanced chart viewer (no transactions, maximized)
- `lib/geckoterminal.ts` - GeckoTerminal API client
- `CLAUDE.md` - App-specific documentation (updated July 26)
- `netlify.toml` - Fixed deployment configuration

## Enhanced Analysis System (READY FOR USE)
- `enhanced-crypto-analyzer.py` - Main analysis class with 1-10 scoring
- `run-enhanced-analysis.py` - Batch runner for enhanced analysis
- Database columns already exist (discovered during deployment):
  - `analysis_score` - For 1-10 rating
  - `analysis_legitimacy_factor` - For High/Medium/Low
  - `analysis_model` - For tracking which AI model used

## Primary Files (ACTIVE)
- `all-in-one-server.py` - **LEGACY** - Uses SQLite database (DO NOT USE for new development)
- `krom-dashboard-main.html` - Token-gated dashboard with ROCKET2 requirement
- `krom-analytics.html` - KROM-styled alternative dashboard
- `krom-standalone-dashboard.html` - Analytics dashboard without token gating
- `krom_calls.db` - **LEGACY** SQLite database (DO NOT USE - all apps use Supabase)

## Edge Functions (Active)
- `crypto-orchestrator-with-x.ts` - Main orchestrator
- `crypto-poller.ts` - KROM API poller  
- `crypto-analyzer.ts` - Claude analysis
- `crypto-x-analyzer-nitter.ts` - X research (using ScraperAPI)
- `crypto-notifier-complete.ts` - Dual bot Telegram notifications

## Documentation
- `CLAUDE.md` - Main documentation (UPDATED - shows deployment complete)
- `ACTIVE_FILES.md` - This file (UPDATED NOW)
- `logs/SESSION-LOG-2025-07.md` - Today's sessions (UPDATED)
- `logs/SESSION-LOG-INDEX.md` - Session index (UPDATED)

## Configuration
- `.env` - Environment variables with all API keys (fixed comment headers)
- `package.json` - Node dependencies (in krom-analysis-app)
- `claude-config.json` - Claude configuration
- `deploy-price-single.sh` - Edge function deployment script

## How to Run

### Web App (Live)
```bash
# Access deployed app:
https://lively-torrone-8199e0.netlify.app

# To deploy updates:
cd krom-analysis-app
git add -A && git commit -m "your message"
git push origin main
# Netlify auto-deploys from GitHub
```

### Local Dashboards (LEGACY - Uses SQLite)
```bash
# WARNING: This server uses the LEGACY SQLite database
# For production data, use the deployed krom-analysis-app instead
python3 all-in-one-server.py

# Access dashboards at:
http://localhost:5001/main        # ROCKET2 token-gated dashboard
http://localhost:5001/krom        # KROM-styled dashboard 
http://localhost:5001/standalone  # No-wallet analytics dashboard
```

## Database Status (SUPABASE ONLY)
- **Total Calls**: 5,103+ (in Supabase crypto_calls table)
- **Database**: All data operations use Supabase cloud database
- **Analyzed with Call scores**: Growing (real-time analysis)
- **X raw tweets available**: 5,232 calls
- **X analysis needed**: 5,223 calls
- **Contract addresses**: Stored in `raw_data.token.ca`
- **Networks**: Stored in `raw_data.token.network`

## Current System Status (August 5, 2025)

### Active Edge Functions (Supabase)
- `crypto-orchestrator` - Main coordinator (every 30 minutes)
- `crypto-poller` - KROM API polling (as needed)  
- `crypto-analyzer` - Claude call analysis (every hour, 50 calls)
- `crypto-x-analyzer-nitter` - X research analysis (every 2 hours, 20 calls)
- `crypto-ath-update` - ATH monitoring (every minute, 25 tokens)
- `crypto-ath-notifier` - Telegram ATH alerts (triggered by updates)
- `crypto-volume-checker` - Volume/liquidity tracking (batch processing)

### Native Cron Jobs (Supabase pg_cron)
- ✅ All 4 cron jobs migrated from external service
- ✅ Zero external dependencies for scheduling
- ✅ Real-time monitoring via Supabase logs
- ✅ Improved reliability and frequency

### Recent System Maintenance
- ✅ Fixed OpenRouter API key (analysis working again)
- ✅ Corrected crypto-poller buy_timestamp bug
- ✅ Backfilled 12 missing timestamp records
- ✅ All systems operational and catching up
- ✅ Analysis backlog: ~300 pending (processing automatically)

### Configuration Files
- `SUPABASE_CRON_SETUP.md` - Documentation for native cron setup
- `.env` - Environment variables with updated API keys
- `CLAUDE.md` - Updated system documentation (v8.2.0)
- `logs/SESSION-LOG-2025-08.md` - Complete August session history

### Monitoring & Status
- **Total Calls**: 5,700+ tokens in crypto_calls table
- **ATH Monitoring**: Continuous processing of all tokens
- **Analysis Pipeline**: Auto-processing new calls and X research
- **Notification System**: @KROMATHAlerts_bot for new ATHs >10%
- **System Health**: All functions operational, zero external dependencies