# KROMV12 Active Files
**Last Updated**: August 20, 2025
**Version**: 12.6.0 - God Mode Admin Features + Orchestrator Consolidation

⚠️ **DATABASE NOTICE**: All KROM apps use SUPABASE exclusively. The local SQLite database is LEGACY only.
⚠️ **RLS ENABLED**: Write operations require SUPABASE_SERVICE_ROLE_KEY (not anon key).

## Currently Active Edge Functions

### Crypto Orchestrator (CONSOLIDATED ✅)
- `/supabase/functions/crypto-orchestrator/index.ts`
- Single orchestrator handling: Poller → Claude → X → Website Analysis → Notifier
- Website analysis: 5 sites/minute (300/hour)
- Running every minute via cron

### Ultra-Tracker (TWO-TIER ✅)
- `/supabase/functions/crypto-ultra-tracker/index.ts` - High liquidity (>=$20K) every minute
- `/supabase/functions/crypto-ultra-tracker-low/index.ts` - Low liquidity ($1K-$20K) every 10 minutes
- Processes 3,200 tokens per minute total

### ATH Verifier (OPTIMIZED ✅)
- `/supabase/functions/crypto-ath-verifier/index.ts`
- Added $15K liquidity filter (skips 35% unreliable tokens)
- Processes 25 tokens/minute with GeckoTerminal OHLCV
- Running via cron: `crypto-ath-verifier-every-minute`

## Monitoring Scripts
- `/monitor-ani-ath.py` - Monitors and auto-corrects ANI ATH
- `/fix-aths-with-gecko.py` - Batch ATH correction using GeckoTerminal
- `/recalc-aths-fast.py` - Fast ATH recalculation script

## Deployment Commands
```bash
# From project root directory:
source .env
export SUPABASE_ACCESS_TOKEN=$SUPABASE_ACCESS_TOKEN
npx supabase functions deploy FUNCTION_NAME --no-verify-jwt --project-ref eucfoommxxvqmmwdbkdv
```

## Krom Analysis App (DEPLOYED ✅)
- **Live URL**: https://lively-torrone-8199e0.netlify.app
- **God Mode**: https://lively-torrone-8199e0.netlify.app?god=mode
- **GitHub**: https://github.com/Masssa75/krom-analysis-app
- **Netlify Site ID**: 8ff019b3-29ef-4223-b6ad-2cc46e91807e

### Key Files in krom-analysis-app/
- `app/page.tsx` - Main UI with god mode detection, filters, localStorage persistence
- `app/api/mark-imposter/route.ts` - Admin API for marking imposter tokens
- `app/api/recent-calls/route.ts` - Main API with imposter filtering support
- `components/RecentCalls.tsx` - Table with admin UI elements
- `app/api/analyze/route.ts` - Call analysis API (1-10 scoring)
- `app/api/x-batch/route.ts` - X batch analysis API
- `components/price-display.tsx` - Price/ROI display
- `components/geckoterminal-panel.tsx` - Enhanced chart viewer

## Active Cron Jobs
1. `crypto-ultra-tracker-every-minute` - Price updates (3,200 tokens/min)
2. `crypto-ath-verifier-every-minute` - ATH verification (25 tokens/min)
3. `crypto-orchestrator-every-minute` - Main monitoring pipeline
4. `krom-call-analysis-every-minute` - Call analysis
5. `krom-x-analysis-every-minute` - X analysis
6. `token-revival-checker-hourly` - Resurrect dead tokens

## Current System Status
- ✅ **Website Analysis**: Integrated into main orchestrator, processing 300 sites/hour
- ✅ **God Mode Admin**: Imposter marking functionality deployed with visual indicators
- ✅ **Orchestrator Consolidation**: Single orchestrator handles all monitoring tasks
- ✅ **ATH Verification**: Optimized with liquidity filters, 95% accuracy
- ✅ **Documentation**: Organized with proper archiving of deprecated functions

## Next Session Notes  
**Analysis Score Filters - Database-Wide Filtering Bug**
- **CRITICAL**: Score filters only affect current page, not entire database
- **Issue**: Pagination logic not properly applying filters before counting
- **Files to check**: `/app/api/recent-calls/route.ts` lines 122-134 (count query)
- **Solution needed**: Ensure filters applied to count query match main query
- Reference: [Full bug details →](logs/SESSION-LOG-2025-08-19-ANALYSIS-SCORE-FILTERS.md)