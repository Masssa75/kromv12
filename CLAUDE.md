# KROMV12 Crypto Monitoring System Documentation

⚠️ **CRITICAL DATABASE NOTICE** ⚠️
- **ALL KROM APPS USE SUPABASE** - This is the ONLY production database
- **DO NOT USE `krom_calls.db`** - This local SQLite database is LEGACY/reference only
- When you see any database operations, ALWAYS use Supabase credentials from `.env`
- **RLS IS ENABLED** - Write operations require `SUPABASE_SERVICE_ROLE_KEY` (not anon key)

🔐 **CRITICAL SECURITY RULES** 🔐
- **NEVER hardcode API keys in Python/JS files** - Always use `os.getenv()` in Python or `process.env` in JavaScript
- **Check before committing**: Always run `git diff --staged | grep -E "sk-|api_key|API_KEY|scp-live"` before pushing
- **Use .gitignore** for sensitive files - Add any files with keys to `.gitignore` immediately
- **Use Supabase/Netlify secrets** for production deployments instead of hardcoding credentials

## Overview
KROMV12 is a monorepo containing multiple cryptocurrency analysis and monitoring applications. Each app serves a specific purpose in the crypto analysis ecosystem. Each app has its own CLAUDE.md with specific documentation.

## Project Structure

### Apps in KROMV12:

1. **crypto-monitor/** - Crypto Monitor & Notifier
   - Original monitoring system running on Supabase Edge Functions
   - Polls KROM API for new crypto calls
   - Analyzes calls with Claude API
   - Performs X (Twitter) research via ScraperAPI + Nitter
   - Sends notifications to Telegram with analysis results
   - **Full documentation**: See `crypto-monitor/CLAUDE.md`

2. **krom-analysis-app/** (Next.js - Netlify Deployment)
   - **Live URL**: https://lively-torrone-8199e0.netlify.app
   - **GitHub Repo**: https://github.com/Masssa75/krom-analysis-app (SEPARATE REPO)
   - **Database**: Uses Supabase EXCLUSIVELY (PostgreSQL)
   - Batch historical analysis tool
   - AI-powered scoring (1-10 scale)
   - Contract address extraction with DexScreener links
   - CSV export functionality
   - **Full documentation**: See `krom-analysis-app/CLAUDE.md`

3. **krom-api-explorer/** (Next.js - Netlify Deployment)
   - **Live URL**: https://majestic-centaur-0d5fcc.netlify.app
   - **GitHub Repo**: https://github.com/Masssa75/krom-api-explorer (SEPARATE REPO)
   - **Purpose**: Discover trending tokens from external APIs (GeckoTerminal, DexScreener)
   - Adds tokens as additional "coin of interest" signals
   - Manual import workflow with source attribution
   - **Full documentation**: See `krom-api-explorer/CLAUDE.md`

4. **Future Apps** (Planned):
   - **krom-referral-bot/** - Telegram referral tracking bot
   - **krom-whale-tracker/** - Whale wallet monitoring
   - **krom-sentiment-analyzer/** - Social sentiment analysis
   - **krom-portfolio-tracker/** - Portfolio management tool

### Shared Resources:
- `.env` - Central environment variables (all apps use this)
- `CLAUDE.md` - This documentation (main project context)
- `krom_calls.db` - **LEGACY** Local SQLite database (reference only - DO NOT USE)
- **Supabase instance** - **PRIMARY DATABASE** - All apps use this cloud database

## Repository Management

### ⚠️ IMPORTANT: Multiple Git Repositories
This project uses **multiple separate GitHub repositories**:


1. **Main Monorepo**: `https://github.com/Masssa75/kromv12`
   - Contains: Edge functions, scripts, shared documentation
   - Directory: `/Users/marcschwyn/Desktop/projects/KROMV12/`
   
2. **krom-analysis-app**: `https://github.com/Masssa75/krom-analysis-app`
   - Contains: Next.js analysis application
   - Directory: `/Users/marcschwyn/Desktop/projects/KROMV12/krom-analysis-app/`
   - **Deploy on push**: Netlify auto-deploys from this repo
   
3. **krom-api-explorer**: `https://github.com/Masssa75/krom-api-explorer`
   - Contains: Next.js API explorer application
   - Directory: `/Users/marcschwyn/Desktop/projects/KROMV12/krom-api-explorer/`
   - **Deploy on push**: Netlify auto-deploys from this repo

## Autonomous Development Workflow

### The Golden Rule - ALWAYS Follow This Pattern:
```bash
1. Make code changes
2. CHECK WHICH REPO: pwd  # Ensure you're in the right directory
3. git add -A && git commit -m "feat: description" && git push origin main
4. IMMEDIATELY (within 5 seconds) start streaming logs:
   netlify logs:deploy
   # Watch until you see "Build script success" or an error
5. If build fails:
   - Analyze the error from the logs
   - Fix the issue immediately
   - Repeat from step 1
6. If build succeeds, verify deployment:
   netlify api listSiteDeploys --data '{"site_id": "8ff019b3-29ef-4223-b6ad-2cc46e91807e"}' | jq '.[0].state'
   # Must show "ready"
7. npx playwright test --headed  # Test on DEPLOYED site (use --headless by default)
8. If tests fail:
   - Debug what's wrong
   - Fix and repeat from step 1
```

**NEVER**:
- Wait to push code "until it's ready"
- Test only locally
- Skip deployment verification
- Leave broken code undeployed

### Real-time Build Monitoring
```bash
# Stream deployment logs in real-time
netlify logs:deploy

# Get deployment details
netlify api listSiteDeploys --data '{"site_id": "8ff019b3-29ef-4223-b6ad-2cc46e91807e"}' | jq '.[0:3]'

# Get specific deployment error
netlify api getSiteDeploy --data '{"site_id": "8ff019b3-29ef-4223-b6ad-2cc46e91807e", "deploy_id": "DEPLOY_ID"}' | jq '.error_message'
```

### Your Full Permissions

You have COMPLETE autonomous control:

**Supabase**:
- ✅ Full management key access (in .env)
- ✅ Can run ANY Supabase CLI command
- ✅ Can modify schema, RLS policies, functions
- ✅ Can access service role for admin operations
```bash
# If not installed:
npm install -g supabase

# You can do:
npx supabase db push
npx supabase db execute --sql "YOUR SQL"
```

**Netlify**:
- ✅ Full deployment access
- ✅ Can add/modify environment variables
- ✅ Can trigger deployments
- ✅ Can check deployment status

**GitHub**:
- ✅ Full repository access
- ✅ Can push directly to main
- ✅ Can create branches, PRs
- ✅ Can manage secrets

**You are expected to work autonomously. - However, ALWAYS Provide options and recommendations before implementing.

### Database Schema Management

**IMPORTANT - Database Backups**: 
Before making any significant database changes (clearing data, schema updates, bulk updates):
1. **Always create a backup first** in the `database-backups/` folder
2. Use timestamped filenames: `backup_name_$(date +%Y%m%d_%H%M%S).json`
3. Example backup command:
```bash
source .env && curl -s "https://eucfoommxxvqmmwdbkdv.supabase.co/rest/v1/crypto_calls?select=*&limit=10000" \
  -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" | jq '.' > \
  database-backups/crypto_calls_backup_$(date +%Y%m%d_%H%M%S).json
```

**Before adding new columns**: Always check if existing fields can serve your purpose. With 70+ columns, there's often an unused field or JSONB column that can store your data.

When you need to add new columns to existing tables in Supabase, use the Management API:

```bash
# Using curl with the Supabase Management API
curl -X POST "https://api.supabase.com/v1/projects/eucfoommxxvqmmwdbkdv/database/query" \
  -H "Authorization: Bearer sbp_97ca99b1a82b9ed514d259a119ea3c19a2e42cd7" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "ALTER TABLE table_name ADD COLUMN IF NOT EXISTS column_name DATA_TYPE;"
  }'
```

**Example - Adding user comment columns:**
```bash
curl -X POST "https://api.supabase.com/v1/projects/eucfoommxxvqmmwdbkdv/database/query" \
  -H "Authorization: Bearer sbp_97ca99b1a82b9ed514d259a119ea3c19a2e42cd7" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "ALTER TABLE crypto_calls ADD COLUMN IF NOT EXISTS user_comment TEXT; ALTER TABLE crypto_calls ADD COLUMN IF NOT EXISTS user_comment_updated_at TIMESTAMPTZ;"
  }'
```

**Important Notes:**
- The Management API token is in `.env` as `SUPABASE_ACCESS_TOKEN`
- You can run multiple SQL statements separated by semicolons
- The API returns an empty array `[]` on success
- Always verify the columns were created by querying them afterward

**Verification example:**
```bash
curl -X GET "https://eucfoommxxvqmmwdbkdv.supabase.co/rest/v1/crypto_calls?select=new_column&limit=1" \
  -H "apikey: [SUPABASE_SERVICE_ROLE_KEY]"
```

**Best Practices:**
1. Always check if columns exist before creating them (use IF NOT EXISTS)
2. Verify changes succeeded before updating application code
3. Update API code to handle both old and new schema gracefully


## Working with This Project - Important Notes

### Row Level Security (RLS) is ENABLED
- **Read access**: Public (anon key or service_role key)
- **Write access**: Service role only (requires `SUPABASE_SERVICE_ROLE_KEY`)
- **Python scripts**: Must use service_role key for INSERT/UPDATE/DELETE operations
- **Web app & Edge Functions**: Already use service_role key, no changes needed

### User Preferences
- **Always explain before executing** - User prefers understanding what will happen before code changes
- **NEVER show mock/fake data** - Always show real data or indicate when data is unavailable. Mock data is extremely misleading and should never be used in any UI or API responses
- **NO COSMETIC FIXES** - Never manually override scores or apply band-aid fixes to hide system issues. The goal is to fix the underlying system, not mask problems. Cosmetic fixes make it harder to identify and solve real issues

### Communication Style
- Ask for clarification when requirements are ambiguous
- Provide options and recommendations before implementing
- Explain technical decisions and trade-offs
- Keep responses concise but informative

### Session Management
- **Code word "WRAP"** - When user says "WRAP it up" or similar, perform end-of-session cleanup:
  1. Move detailed session work to `/logs/SESSION-LOG-YYYY-MM.md`
  2. Update `/logs/SESSION-LOG-INDEX.md` with session summary
  3. Update CLAUDE.md with brief references to moved content
  4. Update ACTIVE_FILES.md to reflect current working files
  5. Move obsolete files to archive/ folder
  6. Update version number and "Last Updated" date
  7. Mark all todos as completed if session work is done and delete them afer they've been moved to the logs

- **Mid-Task WRAP** - If wrapping during incomplete work:
  1. Keep incomplete todos as "pending" or "in_progress"
  2. Add detailed "Next Session Notes" section to CLAUDE.md with:
     - Current progress summary
     - Specific next steps to continue
     - Any important context/decisions made
     - Files that were partially modified
     - Commands or tests that still need to be run
  3. Update "Last Updated" with current status (e.g. "In progress: Feature X")

- **Session Logging Guidelines**:
  - Keep CLAUDE.md focused on current state and essential documentation
  - Move completed work details to session logs with date stamps
  - Each major section moved should be replaced with a 1 line summary and link
  - Session logs preserve full history while keeping main doc clean


## Database Schema (Supabase)
**Table: `crypto_calls`** - Shared by all KROMV12 apps (70+ columns)

### Column Groups:
- **Core Fields** (9): id, krom_id, source, network, contract_address, ticker, buy_timestamp, raw_data, created_at
- **Call Analysis** (13): analysis_score, analysis_tier, analysis_model, analysis_reasoning, analyzed_at, etc.
- **X Analysis** (18): x_analysis_score, x_analysis_tier, x_raw_tweets, x_analysis_reasoning, x_analyzed_at, etc.
- **Price & ROI** (13): price_at_call, current_price, ath_price, ath_roi_percent, roi_percent, price_updated_at, etc.
- **Market Data** (7): market_cap_at_call, current_market_cap, volume_24h, liquidity_usd, pool_address, etc.
- **User Interaction** (5): is_coin_of_interest, coin_of_interest_notes, user_comment, etc.
- **System Fields** (5): notified, notified_premium, is_invalidated, ath_last_checked, etc.

For full schema with data types and constraints, check the database directly on Supabase.

## Edge Functions

### Crypto Monitor Functions
See `crypto-monitor/CLAUDE.md` for details on:
- crypto-orchestrator, crypto-poller, crypto-analyzer
- crypto-x-analyzer-nitter, crypto-notifier

### ATH Tracking Functions (Two-Tier System)
1. **crypto-ultra-tracker** - High-priority tokens >=$20K liquidity (runs every minute)
2. **crypto-ultra-tracker-low** - Low-priority tokens $1K-$20K liquidity (runs every 10 minutes)
3. **crypto-ath-notifier** - Telegram notifications for new ATHs >250% ROI + 20% increase

For implementation details, see [ATH Tracking Session →](logs/SESSION-LOG-2025-08.md)

## Environment Variables
For all required environment variables and API keys:
- **Local development**: Check `.env` file in project root
- **Supabase Edge Functions**: Use `supabase secrets list` to view configured secrets
- **To sync**: Use `supabase secrets set KEY=value` to add/update secrets from `.env`

### Which Supabase Key to Use (RLS Enabled)
- **SUPABASE_ANON_KEY**: 
  - ✅ Reading data (SELECT queries)
  - ✅ Client-side code (browser, React components)
  - ❌ Writing data (INSERT/UPDATE/DELETE) - blocked by RLS
- **SUPABASE_SERVICE_ROLE_KEY**: 
  - ✅ All database operations (bypasses RLS)
  - ✅ Server-side code only (API routes, Edge Functions, scripts)
  - ❌ NEVER use in client-side code - full database access if exposed

## External Services

For detailed API configurations and endpoints:
- **Crypto Monitor APIs**: See `crypto-monitor/CLAUDE.md`
- **Other APIs**: Check `.env` file for keys and configurations


## File Structure
```
KROMV12/
├── crypto-monitor/             # Crypto monitoring system documentation
│   ├── CLAUDE.md             # Complete documentation for edge functions
│   └── README.md             # Overview and links
│
├── krom-analysis-app/          # Next.js app for batch analysis
│   ├── app/api/               # API routes (analyze, download-csv)
│   ├── lib/                   # Utilities
│   ├── package.json          
│   └── CLAUDE.md             # App-specific documentation
│
├── krom-api-explorer/         # Next.js app for external API integration
│   └── CLAUDE.md             # App-specific documentation
│
├── supabase/functions/        # Edge Functions (deployed to Supabase)
│   ├── crypto-*              # Crypto monitor functions
│   └── _shared/              # Shared utilities
│
├── logs/                      # Session logs
│   ├── SESSION-LOG-*.md      # Monthly session logs
│   └── SESSION-LOG-INDEX.md  # Session overview
│
├── archive/                   # Old/deprecated files
│
├── Core Files:
│   ├── .env                  # Environment variables (single source of truth)
│   ├── CLAUDE.md             # This documentation
│   └── krom_calls.db         # LEGACY SQLite database (DO NOT USE)
│
└── Scripts & Tools:
    ├── batch-*.py            # Various batch processing scripts
    └── *.sql                 # Database schema files
```

## How to Use This Documentation

1. **For New Sessions**: Start by reading the "Working with This Project" section
2. **For Debugging**: Check "Common Issues & Solutions" first
3. **For Database Work**: ALWAYS use Supabase (never the local SQLite database)
4. **For Database Changes**: See "Database Schema Management" in Autonomous Development Workflow
5. **For Context**: Review "Current State & Optimizations" to understand decisions made


## Development History

For detailed development history and implementation decisions, see:
- [Session Log Index](logs/SESSION-LOG-INDEX.md) - Overview of all sessions
- [May 2025 Sessions](logs/SESSION-LOG-2025-05.md) - Early development
- [July 2025 Sessions](logs/SESSION-LOG-2025-07.md) - Analysis app development  
- [August 2025 Sessions](logs/SESSION-LOG-2025-08.md) - ATH tracking implementation
- [August 16-17 Token Analysis](logs/SESSION-LOG-2025-08-16-TOKEN-WEBSITE-ANALYSIS.md) - Website discovery investigation


## Security Feature Implementation (July 31, 2025) - PAUSED
Token security analysis using GoPlus API - 38% coverage, UI deployed but modal broken. [Details →](logs/SESSION-LOG-2025-07-31.md)

## DexScreener Volume & Liquidity Integration (July 31, 2025)
Added volume/liquidity tracking via DexScreener API - 100% coverage achieved. [Details →](logs/SESSION-LOG-2025-07-31.md)

## Social Data Integration (August 13, 2025)
Fixed crypto-poller to store social URLs - 4,000+ tokens populated. [Details →](logs/SESSION-LOG-2025-08.md#august-13-2025---social-data-integration-complete)

## ATH Tracking & Notification System (August 4-5, 2025)
Implemented 3-tier ATH tracking with Telegram alerts - 70% efficiency gain. [Details →](logs/SESSION-LOG-2025-08.md)

## Supabase Native Cron Jobs (August 5, 2025)
Migrated from cron-job.org to Supabase pg_cron - 4 jobs running at 5-20ms. [Details →](SUPABASE_CRON_SETUP.md)

## Website Analysis System (August 15-19, 2025)
Deployed crypto-website-analyzer with 4-tier system. [Details →](logs/SESSION-LOG-2025-08.md#august-19-2025---website-analysis-integration--ui-enhancements)

## System Maintenance & Cron Migration (August 5, 2025)
Fixed OpenRouter API, migrated to Supabase cron, achieved zero external dependencies. [Details →](logs/SESSION-LOG-2025-08.md)

## Ultra-Tracker & Two-Tier Processing System (August 6, 2025)
Fixed ATH tracking with pool addresses - 100% coverage, self-optimizing performance. [Details →](logs/SESSION-LOG-2025-08-06.md)

## Edge Function Database Write Fix (August 7, 2025)
Resolved RLS write failures with auth options - ANI token corrected to 23,619% ROI. [Details →](logs/SESSION-LOG-2025-08-07.md)

## ATH Verification System (August 7, 2025)
Deployed crypto-ath-verifier - 25 tokens/minute, full DB scan in 2.2 hours. [Details →](logs/SESSION-LOG-2025-08-07.md#evening-session-edge-function-fixes--ath-verification-system)

## KROM Public Roadmap (August 8, 2025)
Implemented interactive roadmap with 11 features. Live at: https://lively-torrone-8199e0.netlify.app/roadmap [Details →](logs/SESSION-LOG-2025-08.md#august-8-2025---krom-roadmap-implementation)

## KROM UI Enhancements (August 8, 2025 - Evening)
Added Telegram button, floating action menu, contract display, buy button. [Details →](logs/SESSION-LOG-2025-08.md#august-8-2025-evening---krom-ui-enhancements)

## CA Verification & Liquidity Analysis (August 14, 2025)
Enhanced verification with manual tracking - 95% accuracy, liquidity scam patterns identified. [Details →](logs/SESSION-LOG-2025-08.md#august-14-2025-afternoonevening---manual-verification--liquidity-analysis)

## Stage 1 Website Analysis Triage System (August 15, 2025)
Built 7-category scoring system with Kimi K2 - $0.003/analysis. [Details →](logs/SESSION-LOG-2025-08.md#august-15-2025-continued---stage-1-website-analysis-triage-system)

## Token Discovery & Website Analysis Pipeline (August 15, 2025)
Built system monitoring 38,589 daily launches - only 1.2% have websites. [Details →](logs/SESSION-LOG-2025-08-15-TOKEN-DISCOVERY.md)

## Social Media Filters (August 15, 2025 - Evening)
Implemented multi-select filters for Website, Twitter/X, Telegram. [Details →](logs/SESSION-LOG-2025-08.md#august-15-2025---evening---social-media-filters-implementation)

## Stage 1 Website Analysis - Production Ready (August 15, 2025 - Evening)
Enhanced with smart loading detection - 95% success rate. [Details →](logs/SESSION-LOG-2025-08.md#august-15-2025---evening---stage-1-website-analysis-system-improvements)

## ATH Verifier Optimization (August 14, 2025)
Added $15K liquidity filter - 35% fewer false notifications. [Details →](logs/SESSION-LOG-2025-08.md#august-14-2025---ath-verifier-optimization)

## Website Analysis System (August 15-19, 2025)
Integrated with retry logic and 60-second timeout. [Details →](logs/SESSION-LOG-2025-08-19-SESSION-3.md)

## Call Analysis System Restored (August 21, 2025)
Fixed OpenRouter API key issue - 130+ failed analyses restored. [Details →](logs/SESSION-LOG-2025-08-21-CALL-ANALYSIS-FAILURE-FIX.md)

## Website Analysis Tooltip Enhancement (August 21, 2025)
Redesigned tooltips with Quick Take and Found/Missing columns. [Details →](logs/SESSION-LOG-2025-08-21-WEBSITE-ANALYSIS-TOOLTIP-ENHANCEMENT.md)

## GeckoTerminal Search & Data Quality Fix (August 21, 2025)
Fixed search and replaced scam YZY ($9K) with legitimate ($128M). [Details →](logs/SESSION-LOG-2025-08-21-GECKO-TRENDING-YZY-SEARCH-FIX.md)

## Analysis Score Filters & Token Type Hierarchy (August 21, 2025)
Fixed decimal filter issues, added imposter filter, hierarchical classification. [Details →](logs/SESSION-LOG-2025-08-21-ANALYSIS-SCORE-FILTERS-AND-TOKEN-TYPE-HIERARCHY.md)

## N/A Market Cap Display Fix (August 21, 2025)
Fixed N/A displays with multiple fallbacks - all fields properly initialized. [Details →](logs/SESSION-LOG-2025-08-21-NA-MARKET-CAP-FIX.md)

## X Analysis Critical Fix (August 21, 2025)
Fixed search methodology - now uses f=top for quality engagement content. [Details →](logs/SESSION-LOG-2025-08-21-X-ANALYSIS-CRITICAL-FIX.md)

## ATH Tracking Fixed (August 19, 2025)
Split into two tiers at $20K liquidity to fix CPU limits. [Details →](logs/SESSION-LOG-2025-08.md#august-19-2025---ath-tracking-fix)

## Token Website Analysis Complete (August 19, 2025)
Analyzed 218 websites - 18 qualify for Stage 2 (8% pass rate). [Details →](logs/SESSION-LOG-2025-08-19-API-KEY-SECURITY.md)

---
**Last Updated**: August 21, 2025 (N/A Values & Duplicates Fixed)
**Status**: ✅ Major infrastructure issues resolved, analysis accuracy improvements needed
**Version**: 12.6.0 - Fixed N/A market cap display and GeckoTerminal duplicate creation


## ATH Verifier Fixed (August 12, 2025)
Debugged Math.max logic - 18% corrected, 1,170 tokens/hour. [Details →](logs/SESSION-LOG-2025-08.md#august-12-2025-continued---ath-verifier-fix--deployment)

## KROM Public Interface Development (August 7, 2025)
Deployed landing page with pagination and sorting. [Details →](logs/SESSION-LOG-2025-08.md#session-krom-public-interface---pagination--sorting---august-7-2025-afternoon)

## UI Improvements & Filter Optimization (August 13, 2025 - Evening)
Added 400ms debouncing - smooth filters with no race conditions. [Details →](logs/SESSION-LOG-2025-08.md#august-13-2025-evening---ui-improvements--filter-optimization)

## GeckoTerminal ROI Display Fix Priority
Fixed dead token flags for $1M+ liquidity tokens. [Details →](logs/SESSION-LOG-2025-08-20-GECKOTERMINAL-INTEGRATION.md)

## God Mode Admin Features (August 20, 2025)
Added ?god=mode admin access for marking imposters. [Details →](logs/SESSION-LOG-2025-08.md#august-20-2025---website-analysis-integration--god-mode-admin-features)

## App Store Redesign (August 20, 2025)
Transformed to App Store-style with phone frames and AI descriptions. [Details →](logs/SESSION-LOG-2025-08-20-APP-STORE-REDESIGN.md)

## GeckoTerminal Integration & Data Processing Fixes (August 20-21, 2025)
Fixed case-sensitivity, caught up 1,400 tokens, ROI working. [Details →](logs/SESSION-LOG-2025-08-20-GECKOTERMINAL-INTEGRATION.md)

## Admin UX & ATH Bug Fixes (August 21, 2025)
3-dot menu for admin actions, fixed extreme ATH anomalies (BADGER/NEKO/USAI). [Details →](logs/SESSION-LOG-2025-08-21-GECKOTERMINAL-ROI-AND-DATA-FIXES.md)

## Tooltip Implementation & Badge Fixes (August 22, 2025)
Added interactive tooltips, fixed badge heights to 13px, secured API keys. [Details →](logs/SESSION-LOG-2025-08-22-TOOLTIPS-AND-BADGE-FIXES.md)

## GeckoTerminal New Pools Discovery (August 22, 2025)
Re-enabled with 1-minute polling - ~7,000 tokens/hour discovery rate. [Details →](logs/SESSION-LOG-2025-08.md#august-22-2025---new-data-sources--token-discovery)

## Token Website Monitor Enhancement (August 22, 2025)
Added market data tracking - 90 tokens/minute with liquidity/volume updates. [Details →](logs/SESSION-LOG-2025-08.md#august-22-2025---new-data-sources--token-discovery)

## Stage 2 Deep Analysis System Design (August 25, 2025)
Designed comprehensive Stage 2 analyzer for deep token analysis. Enhanced Stage 1 to extract links, tested with AINU/UIUI/BIO tokens. [Details →](logs/SESSION-LOG-2025-08-25-STAGE2-ANALYSIS-DESIGN.md)

## Token Discovery Analyzer Implementation (August 25, 2025)
Built automatic promotion pipeline for high-quality discovered tokens. 12 promoted, 4/12 showing in UI. [Details →](logs/SESSION-LOG-2025-08-25-TOKEN-DISCOVERY-ANALYZER.md)

## Stage 2 Deep Analyzer Implementation (August 25, 2025)
Successfully built contract analysis system with honeypot detection. UIUI correctly identified with 50% sell tax. Pure AI discovery approach. [Details →](logs/SESSION-LOG-2025-08-25-STAGE2-ANALYZER-IMPLEMENTATION.md)

## Stage 2 UI Integration (August 25, 2025) - Partial
Added Stage 2 display with S2 scores and W2 badges. Column Settings issue remains. [Details →](logs/SESSION-LOG-2025-08-25-STAGE2-UI-INTEGRATION.md)

## Token Discovery Promotion Fix (August 25, 2025)
Fixed critical column mismatch preventing promotions. 10+ tokens now promoted successfully. [Details →](logs/SESSION-LOG-2025-08-25-TOKEN-DISCOVERY-PROMOTION-FIX.md)

## Favorites Feature Implementation (August 27, 2025)
Added comprehensive favorites system with star buttons, localStorage persistence, and sidebar filter. [Details →](logs/SESSION-LOG-2025-08.md#august-27-2025---favorites-feature-implementation)

## Discovery Pools Tooltips & Liquidity Fix (August 25, 2025)
Fixed tooltip display and liquidity data issues for Discovery Pools tokens. Removed incorrect is_dead logic from crypto-poller. [Details →](logs/SESSION-LOG-2025-08-25-DISCOVERY-TOOLTIPS-LIQUIDITY-FIX.md)

## Token Discovery System Recovery & Stage 2 Analysis (August 28, 2025)
Fixed 28-hour discovery outage (JWT issue), optimized network coverage to 100%. Performed Stage 2 analysis identifying imposter patterns. [Details →](logs/SESSION-LOG-2025-08-28-TOKEN-DISCOVERY-FIX-STAGE2-ANALYSIS.md)

## KROM Discovery Interface Mockups (August 29, 2025)
Created Pinterest-style masonry mockups with website previews. Implemented proxy for iframe previews, screenshot mode pending fix. [Details →](logs/SESSION-LOG-2025-08-29-KROM-DISCOVERY-MOCKUPS.md)

## Screenshot Mode Fixed with ApiFlash (August 29, 2025)
Implemented ApiFlash for mobile screenshots, fixed typosquatting issue with fake "screeenly". Mobile viewport (iPhone 12) working perfectly. [Details →](logs/SESSION-LOG-2025-08-29-SCREENSHOT-FIX.md)

## Discovery Interface with Real Data (August 29, 2025)
Connected temp-discovery to real crypto_calls database with sorting, filtering, infinite scroll. Full tier tooltips matching main site. [Details →](logs/SESSION-LOG-2025-08-29-DISCOVERY-INTERFACE.md)

## Discovery Dark Mode & Screenshot Storage (August 30, 2025)
Converted discovery to KROM dark theme, implemented permanent screenshot storage with Supabase Storage. Added loading animations, removed 470 lines of temp code. [Details →](logs/SESSION-LOG-2025-08-30-DISCOVERY-DARK-MODE-SCREENSHOTS.md)

---
**Last Updated**: August 30, 2025 (Discovery Dark Mode & Screenshot Storage Complete)
**Status**: ✅ Discovery interface ready for integration into main app
**Version**: 12.26.0 - Dark theme, permanent screenshots, loading states
**Next Session**: Integrate discovery as toggleable view in main krom1.com interface
