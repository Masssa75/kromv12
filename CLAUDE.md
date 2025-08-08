# KROMV12 Crypto Monitoring System Documentation

⚠️ **CRITICAL DATABASE NOTICE** ⚠️
- **ALL KROM APPS USE SUPABASE** - This is the ONLY production database
- **DO NOT USE `krom_calls.db`** - This local SQLite database is LEGACY/reference only
- When you see any database operations, ALWAYS use Supabase credentials from `.env`
- **RLS IS ENABLED** - Write operations require `SUPABASE_SERVICE_ROLE_KEY` (not anon key)

## Overview
KROMV12 is a monorepo containing multiple cryptocurrency analysis and monitoring applications. Each app serves a specific purpose in the crypto analysis ecosystem.

## 🎬 Complete Market Cap Implementation (August 7, 2025)

Successfully implemented comprehensive market cap tracking across entire database with 98.7% token coverage. System now automatically fetches supply data for new calls, maintains market caps on price updates, and includes dead token revival functionality. Notable additions include SOL ($92B market cap), FARTCOIN ($1.35B), and POPCAT ($473M).

[Full implementation details →](logs/SESSION-LOG-2025-08.md#august-7-2025---evening-500-pm---complete-market-cap-implementation)

## 🎬 KROM Public Interface Development (August 7, 2025)

Successfully deployed KROM public landing page with TOP EARLY CALLS and RECENT CALLS sections, complete pagination system (20 items/page), comprehensive sorting functionality, and data consistency improvements. Added dark themed dropdown, ATH ROI filtering, and optimized database queries.

**🚧 Next Session**: Ready to implement filters (ROI range slider, networks checkboxes, time period filter, AI score filter)

[Full session details →](logs/SESSION-LOG-2025-08.md#session-krom-public-interface---pagination--sorting---august-7-2025-afternoon)

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
   - **Database**: Uses Supabase EXCLUSIVELY (PostgreSQL)
   - Batch historical analysis tool
   - AI-powered scoring (1-10 scale)
   - Contract address extraction with DexScreener links
   - CSV export functionality
   - **Full documentation**: See `krom-analysis-app/CLAUDE.md`

3. **krom-api-explorer/** (Next.js - Netlify Deployment)
   - **Live URL**: https://majestic-centaur-0d5fcc.netlify.app
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

**IMPORTANT DATABASE CLARIFICATION**:
- **krom-analysis-app uses SUPABASE EXCLUSIVELY** - Never the local SQLite database
- The local SQLite database (`krom_calls.db`) is for legacy reference only
- ALL production data operations should target Supabase
- When working with any KROM app, always use Supabase credentials from `.env`

## Autonomous Development Workflow

### The Golden Rule - ALWAYS Follow This Pattern:
```bash
1. Make code changes
2. git add -A && git commit -m "feat: description" && git push origin main
3. IMMEDIATELY (within 5 seconds) start streaming logs:
   netlify logs:deploy
   # Watch until you see "Build script success" or an error
4. If build fails:
   - Analyze the error from the logs
   - Fix the issue immediately
   - Repeat from step 1
5. If build succeeds, verify deployment:
   netlify api listSiteDeploys --data '{"site_id": "8ff019b3-29ef-4223-b6ad-2cc46e91807e"}' | jq '.[0].state'
   # Must show "ready"
6. npx playwright test --headed  # Test on DEPLOYED site (use --headless by default)
7. If tests fail:
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

**You are expected to work autonomously. Don't ask for permission - just do it!**

### Database Schema Management

**CRITICAL**: All database operations must target Supabase. Never use the local SQLite database.

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

### Critical Database Rule
**ALWAYS USE SUPABASE for any data operations**. The SQLite database (`krom_calls.db`) is legacy reference only. When you see database operations:
1. Use Supabase credentials from `.env`
2. Connect to the `crypto_calls` table in Supabase
3. Never use `sqlite3.connect()` or reference `krom_calls.db`
4. If unsure, check `krom-analysis-app/` for proper Supabase usage examples

### Row Level Security (RLS) is ENABLED
**As of August 5, 2025, RLS is active on the crypto_calls table:**
- **Read access**: Public (anon key or service_role key)
- **Write access**: Service role only (requires `SUPABASE_SERVICE_ROLE_KEY`)
- **Python scripts**: Must use service_role key for INSERT/UPDATE/DELETE operations
- **Web app & Edge Functions**: Already use service_role key, no changes needed

### User Preferences
- **Always explain before executing** - User prefers understanding what will happen before code changes
- **NEVER show mock/fake data** - Always show real data or indicate when data is unavailable. Mock data is extremely misleading and should never be used in any UI or API responses

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
  - Each major section moved should be replaced with a 3-4 line summary and link
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

### ATH Tracking Functions
1. **crypto-ath-historical** - Calculate 3-tier historical ATH (daily→hourly→minute)
2. **crypto-ath-update** - Continuous monitoring with 1 API call optimization
3. **crypto-ath-notifier** - Telegram notifications for new ATHs >10%

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

## Known Issues & Notes
- **Database**: Always use Supabase - the local SQLite database is legacy reference only
- **Context**: Each app has its own CLAUDE.md with specific documentation
- **Environment**: Check `.env` for all API keys and configurations

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


## Security Feature Implementation (July 31, 2025) - PAUSED

### Overview
Implemented token security analysis using GoPlus Security API to detect liquidity locks, ownership status, and security warnings. Feature is functional but has limited coverage.

### What Was Completed
1. **Database Schema** - Added 7 security columns to Supabase:
   - `liquidity_locked` (BOOLEAN) - Whether liquidity is locked
   - `liquidity_lock_percent` (NUMERIC) - Percentage of liquidity locked
   - `ownership_renounced` (BOOLEAN) - Whether ownership is renounced
   - `security_score` (INTEGER) - Overall security score (0-100)
   - `security_warnings` (JSONB) - Array of security warnings
   - `security_checked_at` (TIMESTAMPTZ) - When security was checked
   - `security_raw_data` (JSONB) - Raw API response data

2. **GoPlus API Integration**
   - **API**: https://api.gopluslabs.io/api/v1/token_security/{chain_id}
   - **Cost**: FREE (no API key required)
   - **Coverage**: Ethereum, BSC, Polygon, Arbitrum, Base, Avalanche, Solana
   - **Success Rate**: ~38% (62% of tokens have no data, especially Solana pump.fun tokens)

3. **UI Implementation**
   - Added Security column to analyzed calls table
   - Icon system: 🔒 (locked), 🔓 (unlocked), ⚠️ (warning), 🛡️ (shield)
   - Color coding: Green (80+), Yellow (50-79), Red (<50)
   - **Known Issue**: Modal dialog doesn't open on click (client-side hydration issue)

4. **Batch Processing Script**
   - Location: `/Users/marcschwyn/Desktop/projects/KROMV12/batch-security-analysis.py`
   - Processes tokens without security data
   - Orders by newest first
   - ~150 tokens analyzed successfully

### Security Scoring Algorithm
```python
# Start with 100 points
score = 100
# Deduct for issues:
# - Honeypot: -50 points
# - High taxes (>10%): -15 points  
# - Mintable token: -20 points
# - No liquidity lock: -5 points (warning only)
# Bonus for good practices:
# + Liquidity locked: +10 points
# + Ownership renounced: +10 points
```

### Files Created/Modified
- `/batch-security-analysis.py` - Main batch processor
- `/components/security-display.tsx` - React UI component
- `/components/ui/dialog.tsx` - Dialog component
- `/app/api/analyzed/route.ts` - Added security fields to API
- `/app/page.tsx` - Integrated SecurityDisplay component
- `/tests/test-security-display.spec.ts` - Playwright tests

### To Resume This Feature
1. **Fix Dialog Issue**: Debug why security modal doesn't open on click
2. **Create Edge Function**: Deploy `crypto-security-checker` to Supabase
3. **Add to Orchestrator**: Include security check between analyzer and notifier
4. **Alternative APIs**: Consider DexScreener or other APIs for better Solana coverage
5. **Process Remaining Tokens**: ~2,400 tokens still need security analysis

### Key Limitation
GoPlus API has limited coverage for newer tokens, especially Solana pump.fun tokens. Only ~38% of tokens have security data available.

### Deployment Status
- Feature deployed to https://lively-torrone-8199e0.netlify.app
- Security column visible in UI
- Icons display correctly based on security status
- Modal dialog has client-side issue (doesn't open)

## DexScreener Volume & Liquidity Integration (July 31, 2025 - Later Session)

Successfully integrated DexScreener API to track volume and liquidity data:
- Edge Function processes 30 tokens per API call efficiently
- Added volume_24h, liquidity_usd, price_change_24h to database
- Enhanced UI with sortable columns and smart formatting
- 100% token coverage achieved with optimized cron job
- [Full session details →](logs/SESSION-LOG-2025-07-31.md)

## ATH Tracking & Notification System (August 4-5, 2025)

Implemented comprehensive All-Time High tracking with instant Telegram notifications:
- **3-tier ATH calculation** using GeckoTerminal OHLCV data (daily→hourly→minute precision)
- **Optimized processing**: Reduced from 3 to 1 API call for updates (70% efficiency gain)
- **Direct notifications**: Instant alerts via @KROMATHAlerts_bot when tokens hit new ATH >10%
- **Continuous monitoring**: Processes entire database every ~4 hours
- [Full implementation details →](logs/SESSION-LOG-2025-08.md)

## Supabase Native Cron Jobs (August 5, 2025)

Migrated all scheduled tasks from cron-job.org to Supabase pg_cron:
- **crypto-orchestrator-every-minute** - Main monitoring pipeline
- **crypto-ath-update-every-minute** - ATH tracking system  
- **krom-call-analysis-every-minute** - Kimi K2 analysis (Netlify endpoint)
- **krom-x-analysis-every-minute** - X analysis (Netlify endpoint)
- All jobs running successfully with ~5-20ms execution time
- [Setup documentation →](SUPABASE_CRON_SETUP.md)

## System Maintenance & Cron Migration (August 5, 2025)

Completed major infrastructure improvements to eliminate external dependencies:
- **Fixed OpenRouter API**: Restored call/X analysis after 5-day outage
- **Native Cron Jobs**: Migrated from cron-job.org to Supabase pg_cron (4 jobs)
- **Data Integrity**: Fixed buy_timestamp bug, backfilled 12 missing records
- **Zero External Dependencies**: All scheduling now handled by Supabase
- **Improved Reliability**: More frequent analysis schedules for better data freshness
- [Full maintenance details →](logs/SESSION-LOG-2025-08.md)

## Ultra-Tracker & Two-Tier Processing System (August 6, 2025)

Successfully fixed and optimized the ATH tracking system:
- **Pool addresses provide 100% coverage** (vs 40% with contract addresses)
- **Two-tier processing**: Live tokens updated every minute, dead tokens checked hourly
- **Self-optimizing**: System marks tokens dead when no trading activity detected
- **Token revival**: Automatically resurrects tokens when trading resumes
- Processing time improving from 15 min → 6 min as system identifies inactive tokens
- [Full implementation details →](logs/SESSION-LOG-2025-08-06.md)

## Edge Function Database Write Fix (August 7, 2025)

Successfully resolved Edge Functions failing to write to database with RLS enabled. Required adding auth options to Supabase client initialization:
```typescript
const supabase = createClient(supabaseUrl, supabaseKey, {
  auth: {
    persistSession: false,
    autoRefreshToken: false
  }
})
```
- Fixed functions: crypto-ultra-tracker, crypto-ath-verifier
- ANI token ATH corrected: $0.03003 → $0.08960221 (23,619% ROI)
- [Full session details →](logs/SESSION-LOG-2025-08-07.md)

## ATH Verification System (August 7, 2025)

Deployed `crypto-ath-verifier` Edge Function to systematically verify and correct ATH values:
- Processes 25 tokens/minute using GeckoTerminal OHLCV data
- Sends Telegram notifications when discrepancies >50% found
- Excludes invalidated tokens to prevent stuck processing
- Completes full database verification in ~2.2 hours
- [Implementation details →](logs/SESSION-LOG-2025-08-07.md#evening-session-edge-function-fixes--ath-verification-system)

---
**Last Updated**: August 8, 2025
**Status**: ✅ Documentation organized and streamlined
**Version**: 10.1.0 - Complete Market Cap System + Documentation Cleanup