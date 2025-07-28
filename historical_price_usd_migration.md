# Migration Plan: historical_price_usd → price_at_call

## Files that need to be updated:

### 1. **crypto-poller Edge Function** (CRITICAL - Currently in production)
- **File**: `/supabase/functions/crypto-poller/index.ts`
- **Lines**: 103, 108, 127-128
- **Changes needed**:
  - Line 103: `callData.historical_price_usd = priceData.price;` → `callData.price_at_call = priceData.price;`
  - Line 108: `callData.historical_price_usd = null;` → `callData.price_at_call = null;`
  - Line 127-128: Update logging to reference `price_at_call`

### 2. **Batch Processor Scripts** (Used for historical data population)
- **Main file**: `populate-historical-prices-using-created-at.py`
  - Line 45: Query filter `historical_price_usd=is.null` → `price_at_call=is.null`
  - Line 81: Update field `'historical_price_usd': krom_price` → `'price_at_call': krom_price`
  - Line 188: Update field `'historical_price_usd': fetched_price` → `'price_at_call': fetched_price`

### 3. **Other Python Scripts** (Utility/analysis scripts - less critical)
- `check-price-columns.py` - Used to check status
- `copy-prices-batch-update.py` - Already served its purpose
- `copy-historical-to-price-at-call.py` - Already served its purpose
- Various test and check scripts

## Migration Steps:

1. **Update crypto-poller Edge Function** (Highest Priority)
   - This is actively writing new data to the wrong column
   - Deploy immediately after update

2. **Update batch processor** 
   - `populate-historical-prices-using-created-at.py`
   - This is what we'll use to populate remaining ~5,000 tokens

3. **Clean up utility scripts** (Optional)
   - Most are one-time use scripts
   - Can be archived or deleted

4. **Remove column from database** (Final step)
   - After ensuring no active code references it
   - Run: `ALTER TABLE crypto_calls DROP COLUMN historical_price_usd;`

## Verification Steps:
1. Check no other apps reference this column
2. Ensure all new prices go to `price_at_call`
3. Monitor for any errors after deployment