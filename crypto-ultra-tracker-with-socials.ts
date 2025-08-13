// crypto-ultra-tracker UPDATE - Add social data extraction
// This shows the changes to add to the existing function

// In the processAndUpdateBatch function, after line 83 where we get price data:
// const priceChange24h = bestPair.priceChange?.h24 || 0
// const txns24h = bestPair.txns?.h24?.buys + bestPair.txns?.h24?.sells || 0

// ADD THIS SECTION to extract social data:
// ==================================================

// Extract social links from the pair info
let websiteUrl: string | null = null
let twitterUrl: string | null = null
let telegramUrl: string | null = null
let discordUrl: string | null = null

// Check if info.socials exists
const socials = bestPair.info?.socials || []
for (const social of socials) {
  if (!social || !social.type) continue
  
  const socialType = social.type.toLowerCase()
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

// Also check info.websites array (sometimes website is here instead of socials)
if (!websiteUrl && bestPair.info?.websites) {
  const websites = bestPair.info.websites
  if (Array.isArray(websites) && websites.length > 0) {
    // websites can be array of strings or array of objects with url property
    websiteUrl = typeof websites[0] === 'string' 
      ? websites[0] 
      : websites[0]?.url || null
  }
}

// Log if we found social data
if (websiteUrl || twitterUrl || telegramUrl || discordUrl) {
  console.log(`Social links found for ${token.ticker}:`, {
    website: websiteUrl ? '✓' : '✗',
    twitter: twitterUrl ? '✓' : '✗', 
    telegram: telegramUrl ? '✓' : '✗',
    discord: discordUrl ? '✓' : '✗'
  })
}

// ==================================================
// END OF NEW SECTION

// Then UPDATE the updateData object (around line 100) to include social fields:
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

// That's it! The rest of the function remains unchanged.
// The social data will be automatically saved to the database
// along with the price updates.