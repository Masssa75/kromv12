# Crypto-Poller Migration: GeckoTerminal → DexScreener

## Summary of Changes

### 1. API Endpoint Change
**Before (GeckoTerminal):**
```typescript
`https://api.geckoterminal.com/api/v2/networks/${geckoNetwork}/pools/${poolAddress}`
```

**After (DexScreener):**
```typescript
`https://api.dexscreener.com/latest/dex/pairs/${dexNetwork}/${poolAddress}`
```

### 2. Response Structure Changes
**GeckoTerminal:**
```typescript
data.data.attributes.base_token_price_usd
data.data.attributes.fdv_usd
data.data.attributes.market_cap_usd
data.data.attributes.reserve_in_usd
```

**DexScreener:**
```typescript
pair.priceUsd
pair.fdv
pair.marketCap
pair.liquidity.usd (or pair.liquidity if number)
```

### 3. New Social Data Extraction
**Added functionality to extract:**
- `website_url` from `info.socials` or `info.websites`
- `twitter_url` from `info.socials`
- `telegram_url` from `info.socials`
- `discord_url` from `info.socials`
- `socials_fetched_at` timestamp

### 4. Source Tracking Update
- Changed from `"GECKO_LIVE"` to `"DEXSCREENER_LIVE"`
- Still uses `"DEAD_TOKEN"` for failed fetches

## What Stays The Same

✅ **All critical calculations remain identical:**
- Total Supply = FDV / price
- Circulating Supply = Market Cap / price
- Market cap calculation logic
- Supply difference threshold (5%)
- Liquidity death threshold ($1000)

✅ **All database fields populated exactly the same:**
- `price_at_call` - Entry price for ROI
- `total_supply` - Calculated from FDV
- `circulating_supply` - Calculated from market cap
- `liquidity_usd` - Liquidity amount
- `market_cap_at_call` - Initial market cap
- `is_dead` - Based on liquidity threshold
- `supply_updated_at` - Timestamp

## New Benefits

🎉 **Additional data now captured:**
1. Social links stored immediately when calls arrive
2. No need for separate social fetching
3. Single API provider (simpler, consistent)
4. Better API (no rate limits documented)

## Testing Checklist

Before deploying, verify:
- [ ] Price fetching works correctly
- [ ] Supply calculations match previous values
- [ ] Liquidity threshold still marks tokens as dead
- [ ] Social links are extracted and stored
- [ ] No errors with missing data (null handling)
- [ ] Source field updates to "DEXSCREENER_LIVE"

## Deployment Steps

1. **Test locally first:**
```bash
# Test with a recent call that hasn't been processed
supabase functions serve crypto-poller-dexscreener
```

2. **Deploy when ready:**
```bash
# Rename folders to switch
mv supabase/functions/crypto-poller supabase/functions/crypto-poller-gecko-backup
mv supabase/functions/crypto-poller-dexscreener supabase/functions/crypto-poller
supabase functions deploy crypto-poller
```

3. **Monitor logs:**
```bash
supabase functions logs crypto-poller
```

## Rollback Plan

If issues occur:
```bash
# Restore original GeckoTerminal version
mv supabase/functions/crypto-poller supabase/functions/crypto-poller-dexscreener
mv supabase/functions/crypto-poller-gecko-backup supabase/functions/crypto-poller
supabase functions deploy crypto-poller
```

## Important Notes

⚠️ **Network mapping simplified:** DexScreener uses same network names as KROM (no conversion needed for most networks)

⚠️ **Liquidity field handling:** DexScreener returns liquidity as either a number or object with `usd` field - code handles both

⚠️ **Social data is best-effort:** Not all tokens have social links, but we capture what's available

## Expected Log Output

Success case:
```
Fetching from DexScreener: solana -> solana
✅ Got price: $0.0123, FDV: $1234567, MCap: $234567, Liquidity: $5000 for pool ABC123
   Total Supply: 100,000,000, Circulating: 19,000,000
   Social links found - Website: ✓, Twitter: ✓
Added new call: xyz123 - TOKEN on solana - Price: $0.0123 (DEXSCREENER_LIVE), Liquidity: $5000.00, Socials: Web Twitter
```