# KROMV12 Active Files
**Last Updated**: August 7, 2025 (Evening)
**Version**: 8.5.0 - Edge Function Auth Fix & ATH Verifier Deployed

⚠️ **DATABASE NOTICE**: All KROM apps use SUPABASE exclusively. The local SQLite database is LEGACY only.
⚠️ **RLS ENABLED**: Write operations require SUPABASE_SERVICE_ROLE_KEY (not anon key).

## Currently Active Edge Functions

### Ultra-Tracker (FIXED ✅)
- `/supabase/functions/crypto-ultra-tracker/index.ts`
- Fixed auth configuration for database writes
- Processes 3,200 tokens per minute
- Added support for new networks (hyperevm, linea, abstract, tron)

### ATH Verifier (DEPLOYED ✅)
- `/supabase/functions/crypto-ath-verifier/index.ts`
- Processes 25 tokens/minute with GeckoTerminal OHLCV
- Sends Telegram notifications for discrepancies >50%
- Excludes invalidated tokens
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
- **GitHub**: https://github.com/Masssa75/krom-analysis-app
- **Netlify Site ID**: 8ff019b3-29ef-4223-b6ad-2cc46e91807e

### Key Files in krom-analysis-app/
- `app/page.tsx` - Main UI with date column (Thai timezone), price display, GeckoTerminal panel
- `app/api/analyze/route.ts` - Call analysis API (1-10 scoring)
- `app/api/x-batch/route.ts` - X batch analysis API (processes stored tweets)
- `app/api/analyzed/route.ts` - Fetches analyzed calls with price data
- `app/api/cron/analyze/route.ts` - Automated call analysis endpoint
- `app/api/cron/x-analyze/route.ts` - Automated X analysis endpoint
- `components/price-display.tsx` - Price/ROI display using Supabase edge function
- `components/geckoterminal-panel.tsx` - Enhanced chart viewer

## Active Cron Jobs
1. `crypto-ultra-tracker-every-minute` - Price updates (3,200 tokens/min)
2. `crypto-ath-verifier-every-minute` - ATH verification (25 tokens/min)
3. `crypto-orchestrator-every-minute` - Main monitoring pipeline
4. `krom-call-analysis-every-minute` - Call analysis
5. `krom-x-analysis-every-minute` - X analysis
6. `token-revival-checker-hourly` - Resurrect dead tokens

## Next Session Notes
- Monitor ATH verifier notifications for discrepancies
- Check if suspicious high ROI tokens (millions %) get corrected
- Consider creating automated invalidation for unrealistic ROIs