# KROMV12 Active Files
**Last Updated**: July 26, 2025
**Version**: 6.6.0 - UI Enhancements & Price Fetching Complete

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
- `all-in-one-server.py` - Unified server with all endpoints (port 5001)
- `krom-dashboard-main.html` - Token-gated dashboard with ROCKET2 requirement
- `krom-analytics.html` - KROM-styled alternative dashboard
- `krom-standalone-dashboard.html` - Analytics dashboard without token gating
- `krom_calls.db` - SQLite database with 98,040 crypto calls

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

### Local Dashboards
```bash
# Single server for everything:
python3 all-in-one-server.py

# Access dashboards at:
http://localhost:5001/main        # ROCKET2 token-gated dashboard
http://localhost:5001/krom        # KROM-styled dashboard 
http://localhost:5001/standalone  # No-wallet analytics dashboard
```

## Database Status
- **Total Calls**: 5,103 (in Supabase crypto_calls table)
- **Analyzed with Call scores**: Growing (real-time analysis)
- **X raw tweets available**: 5,232 calls
- **X analysis needed**: 5,223 calls
- **Contract addresses**: Stored in `raw_data.token.ca`
- **Networks**: Stored in `raw_data.token.network`

## Completed Today (July 26)
- ✅ Added date column to analyzed calls table with Thai timezone tooltips
- ✅ Enhanced GeckoTerminal chart - removed transactions, maximized space
- ✅ Migrated single token price fetching to Supabase edge function
- ✅ Fixed .env parsing issues - uncommented headers
- ✅ Deployed crypto-price-single with ATH calculation support
- ✅ Fixed Entry/Now price display issues
- ✅ Updated documentation for session wrap-up

## Edge Functions (Active)
- `crypto-orchestrator-with-x.ts` - Main orchestrator
- `crypto-poller.ts` - KROM API poller  
- `crypto-analyzer.ts` - Claude analysis
- `crypto-x-analyzer-nitter.ts` - X research (using ScraperAPI)
- `crypto-notifier-complete.ts` - Dual bot Telegram notifications
- `crypto-price-single` - Single token price fetching (NEW - with ATH support)

## Database Status
- **Total Calls**: 5,103+ (in Supabase crypto_calls table)
- **Call Analysis**: 150+ completed with scores
- **X Analysis**: 149+ completed with scores
- **Price Data**: Edge function ready for all tokens
- **Database Columns**: 15 new price-related columns added