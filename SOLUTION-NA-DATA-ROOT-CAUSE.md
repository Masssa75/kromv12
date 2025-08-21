# ROOT CAUSE: N/A Market Cap Data - Processing Queue Monopolization

## The Real Problem

The N/A values aren't caused by duplicates directly, but by **processing queue monopolization**:

1. **KROM sends duplicate calls**: Same token (e.g., YZY) sent multiple times/minute with different krom_ids
2. **All duplicates enter the queue**: Each duplicate is a separate database record
3. **Ultra-tracker processes oldest first**: Uses `ORDER BY ath_last_checked ASC NULLS FIRST`
4. **Popular tokens monopolize queue**: YZY has 15+ unprocessed duplicates
5. **New tokens can't get processed**: They're stuck behind the duplicate backlog
6. **Result**: New tokens show N/A for hours until manual intervention

## Evidence

- **YZY token**: 12 duplicates added in 10 minutes (more than ultra-tracker can process)
- **Processing rate**: Ultra-tracker processes ~10 tokens/minute
- **Queue status**: 15+ YZY duplicates waiting, blocking other tokens
- **Kanye effect**: YZY has $200M+ liquidity (legitimate), gets lots of KROM attention

## Why Duplicates Don't Get Filtered

The ultra-tracker doesn't know they're duplicates because:
- Each has a unique database ID
- Each has a unique krom_id
- The query doesn't group by pool_address
- It processes them one by one, wasting API calls on the same pool

## SOLUTION 1: Prevent Duplicates (Best)

### Modify crypto-poller (`/supabase/functions/crypto-poller/index.ts`)

Add before line 300:
```typescript
// Check if this pool already exists in database
if (callData.pool_address) {
  const { data: existing } = await supabase
    .from('crypto_calls')
    .select('id, ticker, krom_id, created_at')
    .eq('pool_address', callData.pool_address)
    .single()
  
  if (existing) {
    console.log(`Duplicate detected: ${callData.ticker} with pool ${callData.pool_address}`)
    console.log(`  Existing: krom_id=${existing.krom_id}, created=${existing.created_at}`)
    console.log(`  New: krom_id=${callData.krom_id}`)
    continue // Skip this duplicate
  }
}

// Original insertion
const { data, error } = await supabase.from('crypto_calls').insert(callData).select();
```

## SOLUTION 2: Smart Processing (Better Queue Management)

### Modify ultra-tracker (`/supabase/functions/crypto-ultra-tracker/index.ts`)

Change the query at line 286 to skip already-processed pools:
```typescript
// First, get list of already-processed pool addresses in this run
const processedPools = new Set<string>()

while (allTokens.length < maxTokens) {
  const { data: batch, error: fetchError } = await supabase
    .from('crypto_calls')
    .select('id, ticker, network, contract_address, pool_address, ...')
    .not('pool_address', 'is', null)
    .not('pool_address', 'in', `(${Array.from(processedPools).join(',')})`) // Skip processed pools
    .eq('is_invalidated', false)
    .neq('is_dead', true)
    .gte('liquidity_usd', LIQUIDITY_THRESHOLD)
    .order('ath_last_checked', { ascending: true, nullsFirst: true })
    .range(offset, offset + pageSize - 1)
  
  // Add to processed set
  batch.forEach(token => processedPools.add(token.pool_address))
  
  // ... rest of processing
}
```

## SOLUTION 3: Database Constraint (Permanent Fix)

Add unique constraint to prevent future duplicates:
```sql
-- This will fail if duplicates exist, so clean first
ALTER TABLE crypto_calls 
ADD CONSTRAINT unique_pool_address UNIQUE(pool_address);
```

## Quick Fix (Immediate Relief)

Clean up existing duplicates to unblock the queue:
```bash
# Delete all YZY duplicates except the oldest
curl -X POST "https://api.supabase.com/v1/projects/eucfoommxxvqmmwdbkdv/database/query" \
  -H "Authorization: Bearer $SUPABASE_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query": "DELETE FROM crypto_calls WHERE id IN (SELECT id FROM (SELECT id, ROW_NUMBER() OVER (PARTITION BY pool_address ORDER BY created_at ASC) as rn FROM crypto_calls WHERE ticker = '\''YZY'\'') t WHERE rn > 1);"}'
```

## Implementation Priority

1. **IMMEDIATE**: Delete YZY duplicates to unblock queue
2. **TODAY**: Deploy crypto-poller fix to prevent new duplicates
3. **TODAY**: Deploy ultra-tracker fix to skip duplicate pools
4. **THIS WEEK**: Add database constraint after cleanup

## Monitoring

Check queue health:
```sql
-- Show tokens monopolizing the queue
SELECT ticker, COUNT(*) as duplicates, 
       COUNT(*) FILTER (WHERE ath_last_checked IS NULL) as unprocessed
FROM crypto_calls
WHERE pool_address IS NOT NULL
GROUP BY ticker
HAVING COUNT(*) > 5
ORDER BY unprocessed DESC;
```

## Expected Outcome

After fixes:
- Each pool address appears only once in database
- Ultra-tracker processes each token once
- New tokens get processed within 1-2 minutes
- No more N/A values for new tokens
- YZY updates once per minute instead of 12 times

## Why This Keeps Happening

Every 8-12 hours:
1. A token goes viral (like YZY with Kanye news)
2. KROM members post about it repeatedly
3. Each post creates a new call with unique krom_id
4. Duplicates accumulate faster than processing
5. Queue gets clogged
6. New tokens show N/A
7. Manual intervention temporarily clears it
8. Cycle repeats with next viral token

This solution breaks the cycle by preventing duplicates from entering the system.