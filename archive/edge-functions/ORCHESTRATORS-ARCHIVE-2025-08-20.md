# Archived Edge Functions - August 20, 2025

## Context
On August 20, 2025, we consolidated multiple orchestrator Edge Functions into a single `crypto-orchestrator` that includes website analysis. We also removed the unused crypto-notifier-complete function. These archived versions were deprecated but kept for reference.

## Archived Functions

### crypto-orchestrator-with-x-2025-08-20.ts
- **Purpose**: Extended version with website analysis
- **Features**: Poller + Claude + X + Website Analysis + Notifier-Complete
- **Issue**: Used different notifier endpoint (crypto-notifier-complete) which only sent to premium channel
- **Replaced by**: Updated crypto-orchestrator with website analysis added

### crypto-orchestrator-fast-2025-08-20.ts
- **Purpose**: Faster version that skipped X analysis
- **Features**: Poller + Claude + Notifier (no X analysis, no website analysis)
- **Issue**: Missing critical features (X and website analysis)
- **Status**: Never used in production

### crypto-notifier-complete-2025-08-20.ts
- **Purpose**: Enhanced notifier with premium channel support
- **Features**: Dual channel support (regular + premium), dead token filtering, markdown fallback
- **Issue**: Only sent to premium channel, required ALPHA/SOLID tier tokens
- **Status**: Not sending notifications because all recent tokens were TRASH tier
- **Replaced by**: Original crypto-notifier (simpler, sends all notifications)

## Current Production Setup
The main `crypto-orchestrator` now includes:
1. crypto-poller (fetches new tokens)
2. crypto-analyzer (Claude analysis)
3. crypto-x-analyzer-nitter (X/Twitter analysis)
4. crypto-website-analyzer-batch (Website analysis) - Added Aug 20
5. crypto-notifier (sends Telegram notifications)

The cron job `crypto-orchestrator-every-minute` calls this endpoint every minute.

## Why Consolidated
- Simpler maintenance (one orchestrator instead of three)
- Consistent feature set
- Easier to update cron job by just updating the function code
- No need to manage multiple versions