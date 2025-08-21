# HANDOFF PROMPT - Recurring Data Processing Issue (N/A Market Caps)

## Critical Recurring Issue

**Problem**: Market cap data (ATH MC, NOW MC) showing "N/A" for recent tokens is happening AGAIN. This is the SECOND occurrence in 24 hours.

**Pattern Observed**:
1. First occurrence: ~9 hours ago (resolved by manual processing)
2. Second occurrence: NOW (multiple YZY tokens, imperfect, CHEW all showing N/A)

**Visual Evidence**: 
- 7 duplicate YZY tokens all showing N/A for ATH MC and NOW MC
- All added within last 1-2 hours
- ROI shows "-" (dash) indicating no price data
- Entry MC populated correctly (shows these tokens were processed initially)

## Root Cause Investigation Required

### Theory 1: Ultra-Tracker Stopped Processing
The ultra-tracker might have stopped or crashed again.

**Check commands**:
```bash
# 1. Check when ultra-tracker last ran
source .env && curl -s "https://eucfoommxxvqmmwdbkdv.supabase.co/rest/v1/crypto_calls?select=ath_last_checked&order=ath_last_checked.desc.nullslast&limit=5" -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" | jq '.'

# 2. Check if cron job is active
source .env && psql "$DATABASE_URL" -c "SELECT jobname, schedule, active, jobid, lastrun FROM cron.job WHERE jobname LIKE '%ultra%';" 2>/dev/null

# 3. Count tokens with NULL ath_last_checked
source .env && curl -s "https://eucfoommxxvqmmwdbkdv.supabase.co/rest/v1/crypto_calls?select=count&ath_last_checked=is.null&is_dead=eq.false" -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" | jq '.'
```

### Theory 2: Duplicate Token Issue
Multiple YZY entries suggest duplicate processing is happening.

**Investigation**:
```bash
# Check all YZY tokens
source .env && curl -s "https://eucfoommxxvqmmwdbkdv.supabase.co/rest/v1/crypto_calls?ticker=eq.YZY&select=id,created_at,krom_id,source,current_price,current_market_cap,ath_last_checked,group_name&order=created_at.desc" -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" | jq '.'

# Check for duplicate krom_ids
source .env && curl -s "https://eucfoommxxvqmmwdbkdv.supabase.co/rest/v1/rpc/get_duplicate_krom_ids" -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" -H "Content-Type: application/json" -d '{}' | jq '.'
```

### Theory 3: Edge Function Timeout/Failure Pattern
The ultra-tracker might be timing out consistently at certain times.

**Check Edge Function health**:
```bash
# Test ultra-tracker directly
source .env && curl -X POST "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-ultra-tracker" \
  -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
  -H "Content-Type: application/json" \
  -d '{"maxTokens": 10}' \
  --max-time 120

# Check Supabase Edge Function logs (if available)
# Note: May need Supabase dashboard access
```

## Data Recovery Steps

### Immediate Fix (Same as before)
```bash
# 1. Run the force-process script from previous session
python3 /Users/marcschwyn/Desktop/projects/KROMV12/archive/session-aug21-scripts/force-process-new-tokens.py

# 2. Trigger ultra-tracker manually
source .env && for i in {1..3}; do 
  curl -X POST "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-ultra-tracker" \
    -H "Authorization: Bearer $SUPABASE_SERVICE_ROLE_KEY" \
    -H "Content-Type: application/json" \
    -d '{"maxTokens": 500}' 2>/dev/null
  echo "Batch $i complete"
  sleep 2
done
```

## Permanent Fix Investigation

### 1. Check Processing Queue Logic
**File**: `/supabase/functions/crypto-ultra-tracker/index.ts`

Look for:
- How it handles tokens with NULL `ath_last_checked`
- Whether new tokens get priority
- Any conditions that might skip processing

### 2. Check for Memory Leaks
The ultra-tracker processes 1,800+ tokens. It might be running out of memory.

```typescript
// Look for these patterns in ultra-tracker:
- Large arrays being kept in memory
- No cleanup of processed batches
- Accumulating data structures
```

### 3. Check Cron Job Configuration
```sql
-- Check the cron schedule
SELECT * FROM cron.job WHERE jobname LIKE '%ultra%';

-- Check recent job runs
SELECT * FROM cron.job_run_details 
WHERE jobid IN (SELECT jobid FROM cron.job WHERE jobname LIKE '%ultra%')
ORDER BY start_time DESC 
LIMIT 20;
```

### 4. Database Lock Investigation
Multiple YZY entries suggest rapid inserts. Check for:
- Transaction locks during processing
- Deadlocks between poller and ultra-tracker
- Row-level conflicts

```bash
# Check for active locks
source .env && psql "$DATABASE_URL" -c "
SELECT pid, usename, application_name, client_addr, query_start, state, query 
FROM pg_stat_activity 
WHERE state != 'idle' 
ORDER BY query_start;"
```

## Monitoring Solution Needed

### Add Health Check Endpoint
Create a monitoring endpoint that checks:
1. Last successful ultra-tracker run
2. Number of unprocessed tokens
3. Average processing lag

```typescript
// /api/health/ultra-tracker
{
  "lastRun": "2025-08-21T02:00:00Z",
  "unprocessedTokens": 47,
  "averageLag": "15 minutes",
  "status": "WARNING" // OK | WARNING | CRITICAL
}
```

### Add Alerting
- Alert if ultra-tracker hasn't run in 10 minutes
- Alert if unprocessed tokens > 100
- Alert if same token appears 3+ times

## Timeline Reconstruction

Look for patterns:
1. **When do failures occur?** 
   - Specific times? (e.g., always around midnight UTC)
   - After certain number of tokens processed?
   - When specific networks are processed?

2. **What triggers recovery?**
   - Manual intervention only?
   - Self-recovers after time?
   - Specific actions that unstick it?

## Priority Actions

1. **IMMEDIATE**: Recover current data (run force-process script)
2. **HIGH**: Find root cause of recurring issue
3. **HIGH**: Implement monitoring/alerting
4. **MEDIUM**: Add priority queue for new tokens
5. **MEDIUM**: Implement self-healing mechanism

## Key Files to Review

1. `/supabase/functions/crypto-ultra-tracker/index.ts` - Main processing logic
2. `/supabase/functions/crypto-poller/index.ts` - Might be creating duplicates
3. `/supabase/functions/crypto-orchestrator/index.ts` - Coordination between services
4. Previous fix: `/archive/session-aug21-scripts/force-process-new-tokens.py`

## Success Criteria

1. No tokens with N/A market caps after initial processing
2. Ultra-tracker processes new tokens within 5 minutes
3. No duplicate tokens in database
4. System self-recovers from failures
5. Clear alerting when issues occur

## Context from Previous Sessions

- **August 21 Morning**: Fixed same issue, thought it was one-time lag
- **Pattern**: Issue occurs ~8-12 hours apart
- **Temporary Fix**: Manual processing works every time
- **Observation**: gecko_trending tokens seem unaffected (different processing path?)

---
**CRITICAL**: This is a recurring issue affecting system reliability. Finding and fixing the root cause is essential for production stability.