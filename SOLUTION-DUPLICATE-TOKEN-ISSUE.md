# SOLUTION: Recurring N/A Market Cap Data Issue - Root Cause Found

## Executive Summary

**ROOT CAUSE IDENTIFIED**: The KROM API is sending duplicate calls for the same token with different `krom_id`s. Since our database only has a unique constraint on `krom_id`, these duplicates get inserted as separate records with the same pool address. This causes:

1. **Processing delays** - Ultra-tracker wastes time processing duplicates
2. **N/A market caps** - New tokens don't get processed quickly due to queue bloat
3. **UI confusion** - Same token appears multiple times in the interface

## Evidence of the Problem

### Duplicate Statistics
- **imperfect**: 22 duplicate records (same pool address)
- **YZY**: 14 duplicate records
- **OMALLEY**: 13 duplicate records
- **FRANK**: 11 duplicate records
- Total of 10+ tokens with 8+ duplicates each

### Example: YZY Token
All these KROM IDs point to the SAME pool address:
```
krom_id: 68a68048eb25eec68cb9401e -> pool: DQ9weJhfiU4iL5LUoeshDrm5KxDHCMiSbnnKJz7buMcf
krom_id: 68a67f42eb25eec68cb93f94 -> pool: DQ9weJhfiU4iL5LUoeshDrm5KxDHCMiSbnnKJz7buMcf
krom_id: 68a67dafeb25eec68cb93f19 -> pool: DQ9weJhfiU4iL5LUoeshDrm5KxDHCMiSbnnKJz7buMcf
... (11 more with same pool)
```

## Impact on System

1. **Ultra-tracker inefficiency**: Processes same token multiple times
2. **Delayed processing**: Queue gets bloated with duplicates
3. **Database bloat**: Unnecessary storage of duplicate data
4. **API quota waste**: Multiple API calls for same token
5. **User confusion**: Same token appears multiple times in UI

## SOLUTION: Three-Layer Defense

### Layer 1: Immediate Fix (Prevent Future Duplicates)

**File to modify**: `/supabase/functions/crypto-poller/index.ts`

Add duplicate check before insertion (around line 299):

```typescript
// Before inserting, check if this pool address already exists
if (callData.pool_address) {
  const { data: existing } = await supabase
    .from('crypto_calls')
    .select('id, krom_id')
    .eq('pool_address', callData.pool_address)
    .single()
  
  if (existing) {
    console.log(`Token ${callData.ticker} already exists with pool ${callData.pool_address} (existing krom_id: ${existing.krom_id}, new krom_id: ${callData.krom_id})`)
    continue // Skip this duplicate
  }
}

// Original insertion code
const { data, error } = await supabase.from('crypto_calls').insert(callData).select();
```

### Layer 2: Database Constraint (Permanent Protection)

Add unique constraint on pool_address to prevent any future duplicates:

```sql
-- Add unique constraint (will fail if duplicates exist)
ALTER TABLE crypto_calls 
ADD CONSTRAINT unique_pool_address UNIQUE(pool_address);
```

**Note**: Must clean duplicates first (see Layer 3)

### Layer 3: Clean Existing Duplicates

**SQL to remove duplicates** (keeps oldest record):

```sql
-- First, see what will be deleted
WITH duplicates AS (
  SELECT id, ticker, pool_address, created_at,
         ROW_NUMBER() OVER (PARTITION BY pool_address ORDER BY created_at ASC) as rn
  FROM crypto_calls
  WHERE pool_address IS NOT NULL
)
SELECT COUNT(*) as records_to_delete 
FROM duplicates WHERE rn > 1;

-- Then delete duplicates (keeping oldest)
DELETE FROM crypto_calls
WHERE id IN (
  SELECT id FROM (
    SELECT id, ROW_NUMBER() OVER (
      PARTITION BY pool_address 
      ORDER BY created_at ASC
    ) as rn
    FROM crypto_calls
    WHERE pool_address IS NOT NULL
  ) t
  WHERE rn > 1
);
```

## Implementation Steps

### Step 1: Deploy Poller Fix (5 minutes)
```bash
# 1. Modify the crypto-poller as shown above
# 2. Deploy the updated function
supabase functions deploy crypto-poller
```

### Step 2: Clean Database (10 minutes)
```bash
# Execute cleanup SQL via Supabase Management API
curl -X POST "https://api.supabase.com/v1/projects/eucfoommxxvqmmwdbkdv/database/query" \
  -H "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "DELETE FROM crypto_calls WHERE id IN (SELECT id FROM (SELECT id, ROW_NUMBER() OVER (PARTITION BY pool_address ORDER BY created_at ASC) as rn FROM crypto_calls WHERE pool_address IS NOT NULL) t WHERE rn > 1);"}'
```

### Step 3: Add Constraint (2 minutes)
```bash
# Add unique constraint to prevent future duplicates
curl -X POST "https://api.supabase.com/v1/projects/eucfoommxxvqmmwdbkdv/database/query" \
  -H "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "ALTER TABLE crypto_calls ADD CONSTRAINT unique_pool_address UNIQUE(pool_address);"}'
```

### Step 4: Monitor (Ongoing)
- Watch for any insertion errors in crypto-poller logs
- Check duplicate count daily
- Monitor ultra-tracker processing speed

## Alternative Approach (If Constraint Too Strict)

If unique pool_address constraint causes issues (e.g., legitimate re-listings), use composite constraint:

```sql
-- Unique on pool + network combination
ALTER TABLE crypto_calls 
ADD CONSTRAINT unique_pool_network UNIQUE(pool_address, network);
```

## Monitoring Query

Check for duplicates regularly:

```sql
SELECT pool_address, ticker, COUNT(*) as duplicates
FROM crypto_calls 
WHERE pool_address IS NOT NULL
GROUP BY pool_address, ticker
HAVING COUNT(*) > 1
ORDER BY COUNT(*) DESC;
```

## Expected Outcomes

After implementation:
1. **No more duplicates** - Each pool address appears only once
2. **Faster processing** - Ultra-tracker processes each token once
3. **No N/A values** - New tokens processed within minutes
4. **Cleaner UI** - No duplicate entries in interface
5. **Lower API costs** - No redundant API calls

## Testing

After implementation, verify:

```bash
# 1. Check no duplicates remain
curl -s "https://eucfoommxxvqmmwdbkdv.supabase.co/rest/v1/crypto_calls?select=pool_address&pool_address=neq.null" \
  -H "apikey: $SUPABASE_SERVICE_ROLE_KEY" \
  | jq '. | group_by(.pool_address) | map(select(length > 1)) | length'
# Should return 0

# 2. Try inserting duplicate (should fail)
# Monitor crypto-poller logs for "Token already exists" messages

# 3. Check processing speed
# Ultra-tracker should complete in <60 seconds for all tokens
```

## Root Cause Analysis

**Why this happened:**
1. KROM API sends multiple calls for trending/pumping tokens
2. Each call gets a unique `krom_id` from KROM
3. Our system only checked `krom_id` uniqueness
4. Same token with different `krom_id` = accepted as new
5. Processing queue gets clogged with duplicates
6. New tokens wait longer = N/A market caps in UI

**Why it recurs every 8-12 hours:**
- Popular tokens get multiple KROM calls throughout the day
- As duplicates accumulate, processing slows
- Eventually ultra-tracker can't keep up
- Manual intervention clears backlog temporarily
- Cycle repeats as new duplicates arrive

## Prevention for Future

1. **Monitor duplicate creation** - Alert if >5 duplicates found
2. **Processing health check** - Alert if any token has `ath_last_checked` > 30 min old
3. **Queue size monitoring** - Alert if unprocessed tokens > 50
4. **Consider rate limiting** - Process each pool address only once per hour

---

**Priority**: CRITICAL - This is the root cause of recurring N/A data issues
**Effort**: 30 minutes to implement all fixes
**Risk**: Low - Changes are backward compatible