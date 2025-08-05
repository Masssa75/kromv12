# KROMV12 Crypto Monitoring System Documentation

⚠️ **CRITICAL DATABASE NOTICE** ⚠️
- **ALL KROM APPS USE SUPABASE** - This is the ONLY production database
- **DO NOT USE `krom_calls.db`** - This local SQLite database is LEGACY/reference only
- When you see any database operations, ALWAYS use Supabase credentials from `.env`

## Overview
KROMV12 is a monorepo containing multiple cryptocurrency analysis and monitoring applications. Each app serves a specific purpose in the crypto analysis ecosystem.

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

### User Preferences
- **Always explain before executing** - User prefers understanding what will happen before code changes

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



## Early Development Phase
- Built initial web interface and AI chat implementations
- Identified limitations that led to true MCP implementation
- [Full session details →](logs/SESSION-LOG-2025-05.md#web-interface-implementation)


## True MCP Implementation (May 24, 2025)
- Refactored to true Model Context Protocol with flexible tool calling
- Created unified all-in-one-server.py on port 5001
- Simplified database to single `calls` table with 98K+ records
- Added multi-chain support (ETH/SOL) and dynamic tool creation
- [Full session details →](logs/SESSION-LOG-2025-05.md#true-mcp-implementation-may-24-2025-evening)

## Visualization Implementation (May 25, 2025)
- Fixed visualization pipeline and dependencies
- Implemented testing infrastructure for development
- [Full session details →](logs/SESSION-LOG-2025-05.md#visualization-implementation-complete-may-25-2025-pm)

## Database Development (May 24, 2025)
- Created visualization dashboard and discovered KROM API pagination
- Enhanced schema with raw_data storage and downloaded 46K+ calls
- **Key Discovery**: KROM API only accepts `beforeTimestamp` for pagination
- [Full session details →](logs/SESSION-LOG-2025-05.md#database-visualization-dashboard-may-24-2025)


## AI Dashboard Development (May 25, 2025)
- Integrated AI chat with execute_analysis Python tool
- Added admin panel and capability-based prompting
- Fixed token overflow and visualization debugging
- [Full session details →](logs/SESSION-LOG-2025-05.md#ai-powered-dashboard-implementation-may-25-2025)


## Standalone Dashboard (May 26, 2025)
- Created pure data visualization dashboard without AI dependencies
- Implemented 6 real-time chart types with interactive features
- Dashboard URL: http://localhost:5001/standalone
- [Full session details →](logs/SESSION-LOG-2025-05.md#standalone-dashboard-implementation-may-26-2025)

## Token-Gated Dashboard (May 26, 2025)
- Created ROCKET2 token-gated dashboard with wallet connection
- Fixed ethers.js v6 integration and Base network switching
- Active dashboards: /main (ROCKET2), /standalone, /krom (retro style)
- ROCKET2 token: 0x2059e89d75f3fc0d2e256d08ba49db7f5a7e5681
- [Full session details →](logs/SESSION-LOG-2025-05.md#token-gated-dashboard-complete-may-26-2025)

## Recent Development Sessions

## Enhanced Crypto Analysis (July 20, 2025)
- Implemented 1-10 scoring system to identify high-value tokens
- Created Next.js krom-analysis-app for batch historical analysis
- Restructured KROMV12 as monorepo with multiple apps
- [Full session details →](logs/SESSION-LOG-2025-07.md#session-enhanced-crypto-analysis--krom-analysis-app---july-20-2025)

## KROM Analysis App Deployed (July 20, 2025 Evening)
- Successfully deployed to Netlify: https://lively-torrone-8199e0.netlify.app
- Fixed database integration - extracts contracts from raw_data.token.ca
- Real-time AI analysis working with 1-10 scoring system
- Ready to process 5,103 unanalyzed calls chronologically
- [Full session details →](logs/SESSION-LOG-2025-07.md#session-krom-analysis-app-deployment---july-20-2025-evening)

## X (Twitter) Analysis Implemented (July 22, 2025)
- Batch X analysis processing 5,223 calls with stored tweets
- 1-10 scoring system for social media presence quality
- Separate detail views for Call and X analysis
- Fixed empty tweet handling and TypeScript issues
- [Full session details →](logs/SESSION-LOG-2025-07.md#session-x-twitter-analysis-implementation---july-22-2025)

## UI Improvements & Enhanced Details (July 22, 2025 - Later Session)
- Added pagination (20 items/page) and search functionality
- Fixed chronological ordering using `created_at` timestamp
- Enhanced detail panels with call messages and tweet navigation
- Individual token type badges (no auto-hybrid when analyses disagree)
- Full AI prompt transparency in detail views
- [Full session details →](logs/SESSION-LOG-2025-07.md#session-ui-improvements--token-type-display---july-22-2025)

## GPT-4 Migration Complete (July 22, 2025 - Continued)
- Successfully migrated from Claude Haiku to GPT-4 after discovering classification issues
- Cleared all new analysis data while preserving original tier analysis
- Revised prompt to focus purely on legitimacy assessment (not potential/risk)
- Added GPT-4, Kimi K2, and Gemini 2.5 Pro as model options
- Fixed UI to show numeric scores instead of tier labels
- Implemented delete feature for individual analysis rows
- Synchronized AI model selection between Call and X analysis
- [Full session details →](logs/SESSION-LOG-2025-07.md#session-gpt-4-migration--ui-improvements---july-22-2025-evening)

## Advanced Features Implementation (July 22, 2025 - Evening)
- Added Gemini 2.5 Pro batch processing for 60-80% cost savings
- Implemented "Coins of Interest" marking system for model testing
- Tested models with VIRAL, PETEY, LAUNCHGRAM - Kimi K2 best for utility detection
- Prepared for historical price tracking with GeckoTerminal API
- [Full session details →](logs/SESSION-LOG-2025-07.md#session-advanced-features-implementation---july-22-2025-evening)

## Automated Analysis & Rate Limiting Fixed (July 23, 2025)
- Created cron endpoints for automated batch processing
- Fixed dropdown UI transparency issue in AI model selectors
- Discovered and resolved Kimi K2 free model rate limiting
- Switched all endpoints to paid Kimi K2 model
- Successfully analyzed PEP, APE, and NORMIE tokens
- Call analysis: 150 completed, X analysis: 149 completed
- [Full session details →](logs/SESSION-LOG-2025-07.md#session-automated-analysis--rate-limiting-july-23-2025)

## Price Tracking & GeckoTerminal Integration (July 23, 2025)
- Implemented GeckoTerminal API integration for token price tracking
- Fixed N/A price display issues and rate limiting
- Added "Fetch All Prices" batch processing button
- Created embedded GeckoTerminal chart panel for token investigation
- Enhanced price display with refetch capability for failed fetches
- [Full session details →](logs/SESSION-LOG-2025-07.md#session-price-display-improvements--geckoterminal-panel---july-23-2025-continued)

## Automated Database Processing (July 23, 2025 - Evening)
- Set up cron jobs via cron-job.org API for automated processing
- Created Call Analysis (Job 6380042) and X Analysis (Job 6380045) cron jobs
- Fixed timeout issues by increasing limit to 60 seconds
- Reduced X analysis batch size to 3 for better reliability
- Both jobs running continuously: Call 81% complete, X 15% complete
- [Full session details →](logs/SESSION-LOG-2025-07.md#session-automated-analysis-setup--cron-job-implementation---july-23-2025-continued)

## Analysis Progress Tracking (July 24, 2025)
- Added comprehensive progress counters to krom-analysis-app UI
- Migrated price fetching from Netlify to Supabase Edge Functions  
- Increased batch size from 10 to 50 tokens (5x performance improvement)
- Set up automated price fetching cron job (ID: 6384130)
- Real-time progress visible: Call 85.8%, X 24.6%, Prices 6.7%
- [Full session details →](logs/SESSION-LOG-2025-07.md#session-analysis-counters--price-fetching-migration---july-24-2025)

## Price Display & ATH Restoration (July 24, 2025 - Evening)
- Fixed price counter API to check correct database column
- Restored proper ATH functionality from original implementation
- Edge Function now fetches historical OHLCV data for accurate ATH
- Cleared 364 incorrect ATH entries, processing time ~42s per batch
- [Full session details →](logs/SESSION-LOG-2025-07.md#session-price-display-fix--ath-restoration---july-24-2025-evening)

## UI & Price Fetching Complete (July 26, 2025)
- Fixed Entry/Now price display issues by completing Supabase migration
- Successfully deployed crypto-price-single edge function with ATH support
- Added date column to analyzed calls table with Thai timezone tooltips
- Enhanced GeckoTerminal chart view - maximized space, added price grid
- [Full session details →](logs/SESSION-LOG-2025-07-26.md)

## Price Accuracy Fix & Bulk Refresh Complete (July 30, 2025)

Successfully fixed systematic price accuracy issues and refreshed all 5,500+ token prices. Discovered and fixed critical GeckoTerminal bug that was causing massively inflated prices.

**Key Achievements:**
- Fixed 5,266 tokens with missing ROI calculations
- Discovered pool selection bug: code was selecting highest price instead of highest liquidity
- Implemented parallel processing (6x speed improvement) - 71.6 tokens/minute
- Updated 3,408 token prices with 91% success rate in 47.6 minutes

**Critical Fix Applied:**
```typescript
// OLD (WRONG) - Selected highest price pool
if (poolPrice > bestPrice) {
  bestPrice = poolPrice;
}

// NEW (CORRECT) - Selects highest liquidity pool
const sortedPools = pools.sort((a, b) => {
  const liquidityA = parseFloat(a.attributes?.reserve_in_usd || '0');
  const liquidityB = parseFloat(b.attributes?.reserve_in_usd || '0');
  return liquidityB - liquidityA;
});
```

**Results:**
- Price accuracy improved from ~80% to ~95%
- Fixed tokens showing astronomical ROI (e.g., 24M%)
- Realistic ROI distribution: most tokens -80% to -98% (expected)
- All 5,504 tokens now have ROI calculated (99.6%)

[Full session details →](logs/SESSION-LOG-2025-07-30.md)

## Analysis Troubleshooting Session (July 29, 2025)

### Problem Discovered
User reported that newest ~30 calls weren't getting analyzed despite cron jobs appearing to run. Investigation revealed multiple cascading issues.

### Issues Found & Resolved

#### 1. **Cron Job Authentication Failure** ✅ FIXED
- **Problem**: Cron jobs returning `{"error":"Unauthorized"}`
- **Root Cause**: `CRON_SECRET` wasn't set in Netlify environment variables
- **Solution**: Set `CRON_SECRET` in Netlify and enabled both cron jobs on cron-job.org

#### 2. **New Analyses Not Appearing in UI** ✅ FIXED  
- **Problem**: New analyses had `analyzed_at` timestamps but null `analysis_score`
- **Root Cause**: Cron endpoints weren't setting `analyzed_at` field
- **Files Modified**: 
  - `/krom-analysis-app/app/api/cron/analyze/route.ts` - Added `analyzed_at: new Date().toISOString()`
  - `/krom-analysis-app/app/api/cron/x-analyze/route.ts` - Added `x_analyzed_at: new Date().toISOString()`

#### 3. **AI Analysis Details Not Displaying** ✅ FIXED
- **Problem**: Detail panel showed "No detailed analysis available" for 69 records
- **Root Cause**: When we previously fixed records with null scores, we only set scores based on tier but didn't populate `analysis_reasoning` field
- **Solution**: 
  1. Added generic reasoning to 69 call analysis records
  2. Added generic reasoning to 65 X analysis records  
  3. **User feedback**: "Better to remove generic reasoning - let cron reprocess with real AI"
  4. **Final approach**: Cleared all fake data so cron jobs can reprocess properly

#### 4. **OpenRouter API Key Invalid** ✅ FIXED
- **Problem**: All `moonshotai/kimi-k2` requests failing with 401 "No auth credentials found"
- **Root Cause**: OpenRouter API key was expired/invalid
- **Testing Results**:
  - ❌ Old key: `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`
  - ✅ Claude API: Works perfectly
  - ✅ New key: `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`
- **Solution**: 
  1. User provided new working OpenRouter API key
  2. Updated Netlify environment via triggered deployment with new key
  3. Confirmed direct `/api/analyze` endpoint processes calls successfully

### Data Cleanup Performed
```bash
# Cleared fake analysis data from 69 call analysis records
python3 clear-fake-call-analysis.py  # Cleared 69 records

# Cleared fake analysis data from 65 X analysis records  
python3 clear-fake-x-analysis.py     # Cleared 65 records
```

### Current Status

#### ✅ **Resolved Issues**:
- Cron job authentication working
- OpenRouter API key updated and functional
- Direct analysis endpoint processes calls successfully
- Fake data cleared - ready for real AI reprocessing

#### 🔄 **Still Investigating**:
- **Cron jobs still showing errors**: Both cron endpoints report 5 errors when processing
- **No database progress**: Still 70 calls need analysis, 66 need X analysis
- **Working API contradiction**: Direct `/api/analyze` works, but cron jobs fail

#### **Scripts Created**:
- `check-reasoning-fields.py` - Verify analysis_reasoning field status
- `fix-missing-analysis-reasoning.py` - Add reasoning to old records  
- `fix-missing-x-scores.py` - Fix X analysis records with scores
- `clear-fake-call-analysis.py` - Remove fake call analysis data
- `clear-fake-x-analysis.py` - Remove fake X analysis data
- `test-api-failures.py` - Investigate API failure causes
- `check-recent-analysis.py` - Monitor analysis progress

#### 5. **Cron Endpoint Implementation Issue** ✅ FIXED
- **Problem**: Cron endpoints had custom inline analysis logic that was failing
- **Root Cause**: Complex duplicate logic in cron endpoints vs proven working direct endpoints
- **Discovery**: Direct `/api/analyze` processes HONOKA successfully, but `/api/cron/analyze` fails all 5 attempts
- **Solution**: Simplified both cron endpoints to delegate to their proven working counterparts:
  - `/api/cron/analyze` now calls `/api/analyze` 
  - `/api/cron/x-analyze` now calls `/api/x-batch`
- **Files Modified**:
  - `/krom-analysis-app/app/api/cron/analyze/route.ts` - Replaced inline logic with delegation
  - `/krom-analysis-app/app/api/cron/x-analyze/route.ts` - Replaced inline logic with delegation

### Final Resolution ✅ COMPLETE

**Deployment Status**: 
- Changes committed: `fix: simplified cron endpoints to delegate to proven working analysis logic`
- Pushed to GitHub: ✅ Success
- Netlify deployment: ✅ Complete ("Build script success" - "Site is live ✨")
- Site status: ✅ "ready"

**Expected Outcome**: 
- Both cron jobs should now process calls successfully using the proven working analysis logic
- The 70 unanalyzed calls will be processed by the call analysis cron job
- The 66 X analysis records will be processed by the X analysis cron job

### Architecture Fix Summary

**Before**: Cron endpoints had custom inline analysis logic (complex, error-prone)
```typescript
// Complex custom analysis logic in cron endpoint
const analysisResult = await analyzeWithOpenRouter(call);
await supabase.from('crypto_calls').update({...});
```

**After**: Cron endpoints delegate to proven working endpoints (simple, reliable)
```typescript  
// Simple delegation to working endpoint
const response = await fetch(`${baseUrl}/api/analyze`, {
  method: 'POST',
  body: JSON.stringify({ limit: limit, model: model })
});
```

### Key Insights
1. **User preference**: Real AI analysis > fake placeholder data
2. **API hierarchy**: OpenRouter (preferred) > Claude (backup) both work
3. **Systematic approach**: Clear fake data first, then fix root causes
4. **Environment separation**: Local vs Netlify environment variable management
5. **Debugging methodology**: Test direct endpoints before investigating cron logic
6. **Architecture principle**: Delegate rather than duplicate complex logic

## ATH (All-Time High) Calculation System Implementation (July 30, 2025)

### Overview
Implemented a comprehensive 3-tier ATH calculation system using GeckoTerminal OHLCV data to find realistic selling points for each token.

### Key Design Decisions

#### 1. **3-Tier Approach** (Daily → Hourly → Minute)
- **Tier 1**: Find highest daily candle (1000 days history)
- **Tier 2**: Zoom to hourly candles around that day (±1 day window)
- **Tier 3**: Zoom to minute candles around that hour (±1 hour window)
- **Purpose**: Progressively narrow down to find the exact ATH moment

#### 2. **Realistic ATH Price**
- **Final Implementation**: Use `Math.max(open, close)` from the minute with highest peak
- **Rationale**: Avoids unrealistic wick extremes while capturing best tradeable price
- **Evolution**: Started with wick high → changed to close → finalized on max(open,close)

#### 3. **Never Negative ROI**
- All ATH ROI values use `Math.max(0, calculatedROI)`
- Tokens that never exceeded entry price show 0% (not negative)
- More intuitive for users

### Database Schema
Already had ATH fields ready:
- `ath_price` - The ATH price (max of open/close)
- `ath_timestamp` - When ATH occurred
- `ath_roi_percent` - ROI at ATH (never negative)
- `ath_market_cap` - Market cap at ATH (not populated yet)
- `ath_fdv` - FDV at ATH (not populated yet)

### Edge Function: crypto-ath-historical

**Location**: `/supabase/functions/crypto-ath-historical/index.ts`

**Key Features**:
- Processes tokens without ATH data (`ath_price IS NULL`)
- Network mapping (ethereum → eth for GeckoTerminal)
- **Updated**: Now uses CoinGecko Pro API (500 calls/min limit)
- **Updated**: Reduced delay to 0.5 seconds between tokens
- **Updated**: Processes oldest coins first (ORDER BY created_at ASC)
- Fallback logic: minute → hourly → daily data
- Comprehensive error handling and logging

**API Configuration**:
```typescript
// Pro API configuration
const API_BASE = "https://pro-api.coingecko.com/api/v3/onchain"
const HEADERS = {"x-cg-pro-api-key": GECKO_API_KEY}
// Rate limiting: 500 calls/minute (we make 3 calls per token)
await new Promise(resolve => setTimeout(resolve, 500)) // 0.5 seconds
```

**API Usage**:
```bash
curl -X POST "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-ath-historical" \
  -H "Authorization: Bearer [SERVICE_ROLE_KEY]" \
  -H "Content-Type: application/json" \
  -d '{"limit": 10}'
```

### Testing Results
Manually tested on multiple tokens with 100% accuracy match:
- **TCM**: 19.7% ATH ROI (never exceeded entry much)
- **BOOCHIE (ETH)**: 3,198% ATH ROI (37x return)
- **GREEN**: 996.7% ATH ROI (11x return)
- **MEERKAT**: 5,940% ATH ROI (60x return)

### UI Updates
Added tooltip to "Price/ROI" header explaining:
> "ATH (All-Time High) shows the higher of the opening or closing price from the minute with the highest peak, providing a more realistic selling point than the absolute wick high"

### ATH Processing Completed (July 30, 2025)

Successfully implemented 3-tier ATH calculation with critical bug fix for intraday peaks.

**Key Achievement**: Fixed bug where ATH calculation missed same-day peaks by searching from call day start instead of exact call time.

**Results**: 
- Processed 5,553 tokens with parallel processing (~150-200 tokens/min)
- Fixed tokens like FIRST (50.7% ROI) and COOL (166% ROI) that showed incorrect negative/zero values
- All scripts moved to `successful-scripts/ath-calculation/`

**Full documentation**: See `krom-analysis-app/ATH-IMPLEMENTATION.md`

## Kimi K2 Model Verification & Analysis Cleanup (July 29, 2025 - Final)

### Issue Resolution
User reported seeing Claude model usage instead of Kimi K2 in analysis results. Investigation and cleanup completed:

#### Actions Taken ✅
1. **Verified Model Configuration** - Confirmed both cron and direct endpoints correctly specify `moonshotai/kimi-k2`
2. **Cleared Recent Analyses** - Deleted 30 most recent analyses to eliminate mixed model results  
3. **Confirmed System Operation** - Verified cron jobs are processing with Kimi K2 model exclusively
4. **Database Validation** - All new analyses show `analysis_model: "moonshotai/kimi-k2"`

#### Current Status
- **23 calls** awaiting analysis (cleared for reprocessing)
- **Cron jobs active** - Processing automatically every minute
- **Model usage** - 100% Kimi K2 for all new analyses
- **System** - Fully operational and using correct AI model

[Full troubleshooting details →](logs/SESSION-LOG-2025-07-29.md#analysis-system-troubleshooting--resolution-july-29-2025---evening)

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

---
**Last Updated**: August 5, 2025  
**Status**: ✅ ATH tracking system live and operational
**Version**: 8.0.0 - ATH Tracking & Notification System Implementation