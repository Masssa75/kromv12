# KROMV12 Active Files
**Last Updated**: August 5, 2025
**Version**: 8.1.0 - Row Level Security Enabled

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

## Current Work: Price Data Migration (July 28, 2025)

### Active Migration Scripts
- `repopulate-with-pagination.py` - Smart KROM API pagination for missing data
- `backup-before-price-clear.py` - Database backup before clearing prices
- `clear-price-data-test-50.py` - Tested price clearing on 50 records
- `check-krom-api-trade-section.py` - KROM API structure analysis
- `check-missing-calls-status.py` - Missing trade data analysis

### Modified Files This Session
- `/krom-analysis-app/components/price-display.tsx` - Shows raw_data.trade.buyPrice
- `/krom-analysis-app/app/api/analyzed/route.ts` - Returns raw_data in response
- `/krom-analysis-app/app/page.tsx` - Passes raw_data to PriceDisplay

### Migration Status
- ✅ UI updated to show buy prices from raw_data
- ✅ Repopulated 100+ calls with correct trade data
- ✅ Database backed up: `database-backups/crypto_calls_backup_20250728_114514.json`
- ✅ Test cleared 50 oldest records successfully
- ⏳ Ready to clear all 445 records with price data
- ⏳ Need to implement new price fetching logic
- ⏳ Need to fix edge functions for correct price fetching

## Edge Functions (Active)
- `crypto-orchestrator-with-x.ts` - Main orchestrator
- `crypto-poller.ts` - KROM API poller  
- `crypto-analyzer.ts` - Claude analysis
- `crypto-x-analyzer-nitter.ts` - X research (using ScraperAPI)
- `crypto-notifier-complete.ts` - Dual bot Telegram notifications
- `crypto-price-single` - Single token price fetching (NEW - with ATH support)

## Database Status (SUPABASE ONLY)
- **Total Calls**: 5,103+ (in Supabase crypto_calls table)
- **Database**: All data operations use Supabase cloud database
- **Call Analysis**: 150+ completed with scores
- **X Analysis**: 149+ completed with scores
- **Price Data**: Edge function ready for all tokens
- **Database Columns**: 15 new price-related columns added