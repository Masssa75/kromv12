# KROMV12 Crypto Monitoring System Documentation

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
   - Batch historical analysis tool
   - AI-powered scoring (1-10 scale)
   - Contract address extraction with DexScreener links
   - CSV export functionality
   - See section below for details

3. **Future Apps** (Planned):
   - **krom-referral-bot/** - Telegram referral tracking bot
   - **krom-whale-tracker/** - Whale wallet monitoring
   - **krom-sentiment-analyzer/** - Social sentiment analysis
   - **krom-portfolio-tracker/** - Portfolio management tool

### Shared Resources:
- `.env` - Central environment variables (all apps use this)
- `CLAUDE.md` - This documentation (main project context)
- `krom_calls.db` - Local SQLite database with 98K+ calls
- Supabase instance - Shared cloud database

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

## Database Schema
Table: `crypto_calls`
- `krom_id` (TEXT PRIMARY KEY)
- `ticker` (TEXT)
- `buy_timestamp` (TIMESTAMPTZ)
- `raw_data` (JSONB)
- `analysis_tier` (TEXT) - Claude rating: ALPHA/SOLID/BASIC/TRASH
- `analysis_description` (TEXT)
- `analyzed_at` (TIMESTAMPTZ)
- `x_analysis_tier` (TEXT) - X research rating
- `x_analysis_summary` (TEXT)
- `x_raw_tweets` (JSONB)
- `x_analyzed_at` (TIMESTAMPTZ)
- `notified` (BOOLEAN) - Regular bot notifications sent
- `notified_premium` (BOOLEAN) - Premium bot notifications sent (SOLID/ALPHA only)
- `created_at` (TIMESTAMPTZ)

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
│   ├── krom_calls.db         # SQLite database (98K+ calls)
│   ├── .env                  # Environment variables
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
3. **For Database Changes**: See "Database Schema Management" in Autonomous Development Workflow
4. **For Context**: Review "Current State & Optimizations" to understand decisions made



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

## App Details: krom-analysis-app

### Overview
A Next.js web application for batch analysis of crypto calls, deployed to Netlify to avoid CORS issues. This is one of several apps in the KROMV12 monorepo.

### Location
- `/KROMV12/krom-analysis-app/` - Next.js application subdirectory
- Deploys to Netlify, NOT run locally with Python servers
- See `krom-analysis-app/CLAUDE.md` for detailed app-specific documentation

### Key Features
- Historical batch analysis (5-100 calls at a time)
- AI scoring using Claude/Gemini (1-10 scale)
- Contract address extraction with DexScreener links
- CSV export functionality
- NO MOCK DATA - all real API calls

### Environment Variables
- **Source**: Use values from `/KROMV12/.env` (this directory)
- **Deployment**: Add to Netlify dashboard, NOT local .env files
- Required keys:
  - SUPABASE_URL
  - SUPABASE_SERVICE_ROLE_KEY
  - ANTHROPIC_API_KEY
  - GEMINI_API_KEY

### Important Notes
- This is a subdirectory app that deploys independently
- All API keys come from parent .env file
- Never create .env.local in the app directory
- When deployed, accesses Supabase directly (no CORS)

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

### Next Session Notes
- **Priority**: Verify analysis_score updates are persisting in database
- **Processing**: Systematically analyze all 5,103 calls from oldest first
- **Optimization**: Consider batch processing (10-50 calls at once)
- **UI**: Add progress tracking for bulk analysis operations

---
**Last Updated**: July 20, 2025
**Status**: App deployed and functional, ready for bulk analysis
**Version**: 5.4.0 - KROM Analysis App Live