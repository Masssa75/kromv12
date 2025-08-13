# Update crypto-ultra-tracker to Store Social Data

## Current Situation
The `crypto-ultra-tracker` Edge Function already fetches from DexScreener's pairs endpoint but **ignores the social data** that comes in the response.

## Simple Solution
Modify the existing function to extract and store social links that are already in the API response!

### What to Add to processAndUpdateBatch function:

```typescript
// After line 83 where it extracts price data, add:

// Extract social links from the pair info
const socialLinks = bestPair.info?.socials || []
let websiteUrl = null
let twitterUrl = null
let telegramUrl = null
let discordUrl = null

for (const social of socialLinks) {
  const socialType = social.type
  const socialUrl = social.url
  
  if (socialType === 'website' && !websiteUrl) {
    websiteUrl = socialUrl
  } else if (socialType === 'twitter' && !twitterUrl) {
    twitterUrl = socialUrl
  } else if (socialType === 'telegram' && !telegramUrl) {
    telegramUrl = socialUrl
  } else if (socialType === 'discord' && !discordUrl) {
    discordUrl = socialUrl
  }
}

// Also check for direct website in info.websites
if (!websiteUrl && bestPair.info?.websites) {
  const websites = bestPair.info.websites
  if (Array.isArray(websites) && websites.length > 0) {
    websiteUrl = websites[0].url || websites[0]
  }
}
```

### Update the updateData object (around line 100):

```typescript
const updateData: any = {
  current_price: currentPrice,
  volume_24h: volume24h,
  liquidity_usd: liquidityUsd,
  price_change_24h: priceChange24h,
  price_updated_at: new Date().toISOString(),
  last_volume_check: new Date().toISOString(),
  ath_last_checked: new Date().toISOString(),
  is_dead: isDead,
  // ADD THESE NEW FIELDS:
  website_url: websiteUrl,
  twitter_url: twitterUrl,
  telegram_url: telegramUrl,
  discord_url: discordUrl,
  socials_fetched_at: new Date().toISOString()
}
```

## Benefits
1. **Zero additional API calls** - We're already fetching this data!
2. **Automatic updates** - Runs every minute for live tokens
3. **No new Edge Functions needed** - Just modify existing one
4. **Immediate coverage** - Will populate socials for all active tokens

## Implementation Steps
1. Update the Edge Function with social extraction code
2. Deploy the updated function
3. Social links will automatically populate as tokens are processed
4. Update UI to read from database instead of calling DexScreener

## Alternative: Batch Historical Update
For tokens that haven't been processed recently (dead tokens), we can run a one-time batch script to fetch their social data.

## Summary
The orchestrator's `crypto-ultra-tracker` function is **already making the perfect API call** - we just need to extract and store the social data that's already in the response!