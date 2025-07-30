# KROMV12 Crypto Monitoring System Documentation

⚠️ **CRITICAL DATABASE NOTICE** ⚠️
- **ALL KROM APPS USE SUPABASE** - This is the ONLY production database
- **DO NOT USE `krom_calls.db`** - This local SQLite database is LEGACY/reference only
- When you see any database operations, ALWAYS use Supabase credentials from `.env`

## Overview
KROMV12 is a monorepo containing multiple cryptocurrency analysis and monitoring applications. Each app serves a specific purpose in the crypto analysis ecosystem.

## Project Structure

### Apps in KROMV12:

1. **Crypto Monitor & Notifier** (Currently in root - to be moved to own folder)
   - Original monitoring system
   - Polls KROM API for new crypto calls
   - Analyzes calls with Claude API
   - Performs X (Twitter) research via ScraperAPI + Nitter
   - Sends notifications to Telegram with analysis results
   - Uses Supabase Edge Functions

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

## Architecture Flow (this is for the crypto poller and notifier. should be moved into the project's own folder & claude.md file once created)
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

## Database Schema (Supabase)
**Note**: This schema is for the Supabase cloud database. Do NOT use the local SQLite database.

**Table: `crypto_calls`** (70 columns total - Multi-Source Support)

### Core Fields (9)
Essential fields for basic token tracking:
- `id` (UUID PRIMARY KEY) - Universal unique ID, auto-generated
- `krom_id` (TEXT UNIQUE NOT NULL) - KROM's original ID (NULL for other sources)
- `source` (TEXT DEFAULT 'krom') - Signal source: 'krom', 'geckoterminal', etc.
- `network` (TEXT) - Blockchain network: 'solana', 'ethereum', 'bsc', etc.
- `contract_address` (TEXT) - Token contract address
- `ticker` (TEXT) - Token symbol/ticker
- `buy_timestamp` (TIMESTAMPTZ) - When the call was made
- `raw_data` (JSONB NOT NULL) - Source-specific API response
- `created_at` (TIMESTAMPTZ DEFAULT now()) - Record creation timestamp

### Call Analysis Fields (13)
AI analysis results for legitimacy scoring:
- `analysis_tier` (TEXT) - Claude rating: ALPHA/SOLID/BASIC/TRASH
- `analysis_description` (TEXT) - Analysis summary
- `analyzed_at` (TIMESTAMPTZ) - When initial analysis was completed
- `analysis_score` (INTEGER) - Legitimacy score (1-10)
- `analysis_model` (TEXT) - AI model used (claude-3-haiku, gpt-4, kimi-k2, etc.)
- `analysis_legitimacy_factor` (TEXT) - High/Medium/Low legitimacy
- `analysis_token_type` (TEXT) - meme/utility classification
- `analysis_reasoning` (TEXT) - Detailed analysis reasoning
- `analysis_prompt_used` (TEXT) - Full prompt sent to AI
- `analysis_batch_id` (UUID) - Batch processing identifier
- `analysis_batch_timestamp` (TIMESTAMPTZ) - When batch was processed
- `analysis_duration_ms` (INTEGER) - Processing time in milliseconds
- `analysis_confidence` (NUMERIC) - AI confidence level
- `analysis_reanalyzed_at` (TIMESTAMPTZ) - Last re-analysis timestamp

### X (Twitter) Analysis Fields (18)
Social media presence evaluation:
- `x_analysis_tier` (TEXT) - X research rating
- `x_analysis_summary` (TEXT) - Summary of X analysis
- `x_raw_tweets` (JSONB) - Raw tweet data from API
- `x_analyzed_at` (TIMESTAMPTZ) - When X analysis was completed
- `x_analysis_score` (INTEGER) - Social media score (1-10)
- `x_analysis_model` (TEXT) - AI model used for X analysis
- `x_best_tweet` (TEXT) - Most relevant tweet found
- `x_legitimacy_factor` (TEXT) - Legitimacy based on social presence
- `x_analysis_token_type` (TEXT) - Token type from social analysis
- `x_analysis_reasoning` (TEXT) - Detailed X analysis reasoning
- `x_analysis_prompt_used` (TEXT) - Prompt used for X analysis
- `x_analysis_batch_id` (UUID) - X analysis batch identifier
- `x_analysis_batch_timestamp` (TIMESTAMPTZ) - X batch processing time
- `x_analysis_duration_ms` (INTEGER) - X analysis processing time
- `x_reanalyzed_at` (TIMESTAMPTZ) - Last X re-analysis timestamp
- `x_analysis_legitimacy_factor` (TEXT) - Enhanced legitimacy assessment
- `x_analysis_best_tweet` (TEXT) - Best tweet for analysis
- `x_analysis_key_observations` (JSONB) - Key social media observations

### Price & ROI Fields (13)
Token price tracking and performance metrics:
- `price_at_call` (NUMERIC) - Token price when call was made
- `price_current` (NUMERIC) - Current/latest token price
- `current_price` (NUMERIC) - Alternative current price field
- `price_updated_at` (TIMESTAMPTZ) - When price was last updated
- `price_fetched_at` (TIMESTAMPTZ) - When price data was fetched
- `price_change_percent` (NUMERIC) - Price change percentage
- `price_network` (TEXT) - Network used for price fetching
- `ath_price` (NUMERIC) - All-time high price
- `ath_timestamp` (TIMESTAMPTZ) - When ATH was reached
- `ath_roi_percent` (NUMERIC) - ROI percentage from ATH
- `ath_market_cap` (NUMERIC) - Market cap at ATH
- `ath_fdv` (NUMERIC) - Fully diluted value at ATH
- `roi_percent` (NUMERIC) - Current ROI percentage

### Market Data Fields (7)
Additional market metrics:
- `market_cap_at_call` (NUMERIC) - Market cap when call was made
- `current_market_cap` (NUMERIC) - Current market capitalization
- `fdv_at_call` (NUMERIC) - Fully diluted value at call time
- `current_fdv` (NUMERIC) - Current fully diluted value
- `token_supply` (NUMERIC) - Total token supply
- `pool_address` (TEXT) - DEX pool address for price fetching

### User Interaction Fields (5)
User-generated content and tracking:
- `is_coin_of_interest` (BOOLEAN DEFAULT false) - User-marked interesting tokens
- `coin_of_interest_marked_at` (TIMESTAMPTZ) - When marked as interesting
- `coin_of_interest_notes` (TEXT) - User notes for interesting coins
- `user_comment` (TEXT) - User comments on the call
- `user_comment_updated_at` (TIMESTAMPTZ) - When comment was last updated

### System & Notification Fields (5)
Internal system tracking:
- `notified` (BOOLEAN DEFAULT false) - Regular bot notifications sent
- `notified_premium` (BOOLEAN DEFAULT false) - Premium bot notifications sent (SOLID/ALPHA only)
- `is_invalidated` (BOOLEAN DEFAULT false) - Whether call is invalidated
- `invalidated_at` (TIMESTAMPTZ) - When call was invalidated
- `invalidation_reason` (TEXT) - Reason for invalidation

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
Required in Supabase:
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

## Current State & Optimizations (this is for the crypto poller and notifier. should be moved into the project's own folder & claude.md file once created)

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

### Manual Testing (this is for the crypto poller and notifier. should be moved into the project's own folder once created)
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

## Notification Format (this is for the crypto poller and notifier. should be moved into the project's own folder once created)
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

## Common Issues & Solutions (this is for the crypto poller and notifier. should be moved into the project's own folder once created)

**IMPORTANT - Database Confusion**:
- **Always use Supabase** for any data operations
- The local SQLite database (`krom_calls.db`) is LEGACY and should NOT be used
- If you see `krom_calls.db` mentioned, ignore it and use Supabase instead
- All apps in KROMV12 use the Supabase cloud database

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

## File Structure
```
KROMV12/
├── krom-analysis-app/          # Next.js app for batch analysis
│   ├── app/api/               # API routes (analyze, download-csv)
│   ├── lib/                   # Utilities
│   ├── package.json          
│   └── CLAUDE.md             # App-specific documentation
│
├── edge-functions/            # Supabase Edge Functions
│   ├── crypto-orchestrator-with-x.ts
│   ├── crypto-poller.ts
│   ├── crypto-analyzer.ts
│   ├── crypto-x-analyzer-nitter.ts
│   └── crypto-notifier-complete.ts
│
├── logs/                      # Session logs
│   ├── SESSION-LOG-2025-05.md
│   ├── SESSION-LOG-2025-07.md
│   └── SESSION-LOG-INDEX.md
│
├── archive/                   # Old/deprecated files
│   ├── old-servers/          # Previous server implementations
│   ├── old-interfaces/       # Previous UI versions
│   └── edge-functions/       # Old Edge Function versions
│
├── Core Files:
│   ├── all-in-one-server.py  # Main unified server (port 5001)
│   ├── krom_calls.db         # LEGACY SQLite database (DO NOT USE - reference only)
│   ├── .env                  # Environment variables (includes Supabase credentials)
│   └── CLAUDE.md             # This documentation
│
├── Dashboard Files:
│   ├── krom-standalone-dashboard.html  # Main analytics dashboard
│   ├── krom-dashboard-main.html       # Token-gated dashboard
│   ├── krom-analytics.html            # KROM-styled version
│   └── krom-analysis-viz.html         # Original visualization
│
├── Database Scripts:
│   ├── download-krom-simple.py         # Download KROM calls
│   ├── create-simple-database.sql      # Database schema
│   └── add-enhanced-analysis-columns.sql # Analysis columns
│
└── Analysis Scripts:
    ├── enhanced-crypto-analyzer.py     # AI analysis logic
    ├── batch-analysis-api.py          # Batch processing
    └── export-analysis-data.py        # Data export
```

## Known Issues & Notes
- X analyzer currently rates most calls as TRASH (expected - only 1-2 SOLID/ALPHA per week)
- Premium bot will be significantly quieter than regular bot (SOLID/ALPHA calls only)
- System is optimized for ~1-5 calls per minute normal operation
- All functions work correctly as of last testing
- Dual bot notification system fully operational

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
- 6-second delay between tokens (respects rate limits)
- Fallback logic: minute → hourly → daily data
- Comprehensive error handling and logging

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

### Next Session: Full Database Processing

**Current Status**:
- ✅ Edge function tested and working on 10 tokens
- ✅ Takes ~7.4 seconds per token (including 6s rate limit delay)
- ✅ ~5,700 tokens need ATH calculation
- ⏱️ Estimated time: ~11.8 hours for full database

**Processing Strategy Options**:

1. **Single Large Batch**
   ```bash
   # Process all at once (11+ hours)
   curl -X POST ".../crypto-ath-historical" -d '{"limit": 6000}'
   ```

2. **Multiple Smaller Batches**
   ```bash
   # Process 500 at a time (~1 hour each)
   for i in {1..12}; do
     curl -X POST ".../crypto-ath-historical" -d '{"limit": 500}'
     sleep 300  # 5 min break between batches
   done
   ```

3. **Parallel Processing** (if rate limits allow)
   - Could run 2-3 instances with different token sets
   - Need to ensure they don't process same tokens

4. **Scheduled Cron Approach**
   - Set up cron to process 100 tokens every 15 minutes
   - Would complete in ~14 hours spread over time

**Considerations**:
- GeckoTerminal rate limit: 30 calls/minute (we do 3 calls per token)
- Edge function timeout: Unknown (test with larger batches)
- Some pools may not have OHLCV data (expected failures)
- Monitor for any 429 rate limit errors

**Recommended Approach**: Start with 100-token batches to verify stability, then increase to 500-token batches for overnight processing.

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

---
**Last Updated**: July 29, 2025  
**Status**: 🎯 CURRENT PRICE TASK READY TO COMPLETE - Query bug fixed, batch processing operational
**Version**: 7.7.0 - Current Price Query Bug Fix & Batch Processing Complete