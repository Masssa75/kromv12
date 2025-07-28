# Deploy Enhanced Crypto-Poller

## Backup Status
✅ Original function backed up to: `crypto-poller-backup-original-20250728_150254.ts`

## Deployment Steps

### Option 1: Supabase Dashboard (Recommended)
1. Go to https://supabase.com/dashboard/project/eucfoommxxvqmmwdbkdv/functions
2. Click on `crypto-poller` function
3. Click "Edit" 
4. Copy the entire contents of `edge-functions/crypto-poller.ts`
5. Paste it to replace the existing code
6. Click "Deploy"

### Option 2: Supabase CLI
```bash
cd /Users/marcschwyn/Desktop/projects/KROMV12
supabase login  # if not already logged in
supabase functions deploy crypto-poller
```

## What's Changed
- ✅ Added `fetchCurrentPrice()` function
- ✅ Automatic price fetching for all new calls  
- ✅ Stores price in `historical_price_usd` column
- ✅ Sets `price_source` (GECKO_LIVE, DEAD_TOKEN, NO_POOL_DATA)
- ✅ Enhanced logging with price information

## Testing After Deployment
Run this command to test:
```bash
curl -X POST "https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-poller" \
  -H "Authorization: Bearer $(grep SUPABASE_SERVICE_ROLE_KEY .env | cut -d'=' -f2)" \
  -H "Content-Type: application/json"
```

Look for logs showing:
- "Fetching current price for TOKEN_NAME on network..."
- "✅ Got current price: $X.XX for pool..."
- "Added new call: ID - TOKEN - Price: $X.XX (GECKO_LIVE)"

## Expected Behavior
- Each new call will now have immediate price data
- Dead tokens will be marked as "DEAD_TOKEN"
- No more missing historical prices for future calls