import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.38.0'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

// DexScreener network mapping
const NETWORK_MAP: Record<string, string> = {
  'ethereum': 'ethereum',
  'solana': 'solana',
  'bsc': 'bsc',
  'polygon': 'polygon',
  'arbitrum': 'arbitrum',
  'optimism': 'optimism',
  'avalanche': 'avalanche',
  'base': 'base',
  // Additional networks (may or may not be supported by DexScreener)
  'hyperevm': 'hyperliquid',
  'linea': 'linea',
  'abstract': 'abstract',
  'tron': 'tron',
  'sui': 'sui',
  'ton': 'ton'
}

interface DexScreenerToken {
  chainId: string
  tokenAddress: string
  priceUsd: string
  volume24h: number
  liquidity: number
  priceChange24h: number
  txns24h: number
}

// Helper function to process and update a batch of tokens
async function processAndUpdateBatch(
  data: any,
  batch: any[],
  supabase: any,
  newATHs: any[],
  liquidityDeaths: any[],
  revivals: any[]
): Promise<{ processed: number; updated: number }> {
  let processed = 0
  let updated = 0

  // Process each token's data
  // The pairs endpoint returns data in a different format
  const pairsArray = data.pairs || (data.pair ? [data.pair] : [])
  
  for (const token of batch) {
    try {
      // Find the pair matching this token's pool address
      const matchingPair = pairsArray.find((p: any) => 
        p.pairAddress === token.pool_address
      )

      if (!matchingPair) {
        // Token not found on DexScreener - mark as dead
        console.log(`Token ${token.ticker} not found on DexScreener - marking as dead`)
        await supabase
          .from('crypto_calls')
          .update({ 
            is_dead: true,
            ath_last_checked: new Date().toISOString() 
          })
          .eq('id', token.id)
        continue
      }

      const bestPair = matchingPair

      // Determine if our token is base or quote by comparing contract addresses
      const isBase = bestPair.baseToken.address.toLowerCase() === token.contract_address.toLowerCase()
      const tokenData = isBase ? bestPair.baseToken : bestPair.quoteToken

      const currentPrice = parseFloat(bestPair.priceUsd || '0')
      const volume24h = bestPair.volume?.h24 || 0
      const liquidityUsd = bestPair.liquidity?.usd || 0
      const priceChange24h = bestPair.priceChange?.h24 || 0
      const txns24h = bestPair.txns?.h24?.buys + bestPair.txns?.h24?.sells || 0

      // ====== NEW SECTION: Extract social links ======
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
      // ====== END NEW SECTION ======

      // Skip if no valid price
      if (currentPrice <= 0) continue

      processed++

      // Check liquidity threshold - tokens with less than $1000 liquidity should be marked as dead
      const LIQUIDITY_THRESHOLD = 1000
      const isDead = liquidityUsd < LIQUIDITY_THRESHOLD
      
      if (isDead && liquidityUsd > 0) {
        console.log(`Token ${token.ticker} has low liquidity ($${liquidityUsd.toFixed(2)}) - marking as dead`)
      }

      // Prepare update object - WITH SOCIAL FIELDS ADDED
      const updateData: any = {
        current_price: currentPrice,
        volume_24h: volume24h,
        liquidity_usd: liquidityUsd,
        price_change_24h: priceChange24h,
        price_updated_at: new Date().toISOString(),
        last_volume_check: new Date().toISOString(),
        ath_last_checked: new Date().toISOString(),
        is_dead: isDead,  // Mark based on liquidity threshold
        // ADD SOCIAL FIELDS:
        website_url: websiteUrl,
        twitter_url: twitterUrl,
        telegram_url: telegramUrl,
        discord_url: discordUrl,
        socials_fetched_at: new Date().toISOString()
      }

      // Update current_market_cap if we have circulating supply
      if (token.circulating_supply && currentPrice > 0) {
        updateData.current_market_cap = currentPrice * token.circulating_supply
      }

      // Check for new ATH (only for alive tokens)
      const priceAtCall = token.price_at_call || 0
      let isNewATH = false
      
      // Skip ATH calculations for dead tokens
      if (!isDead && priceAtCall > 0) {
        const currentROI = ((currentPrice - priceAtCall) / priceAtCall) * 100
        
        // Always update current ROI
        updateData.roi_percent = currentROI
        
        // CRITICAL: Only update ATH if we have a genuinely higher price
        // Check for existing ATH - handle null, undefined, 0, or any falsy value
        const existingATH = token.ath_price || 0
        
        // Only proceed if current price is actually higher than existing ATH
        // OR if there's no ATH at all (existingATH === 0)
        if (existingATH === 0 || currentPrice > existingATH) {
          // Determine what the new ATH should be
          const newATH = existingATH === 0 
            ? Math.max(currentPrice, priceAtCall)  // Initialize to at least entry price
            : currentPrice  // We already know currentPrice > existingATH
          
          // Final safety check: only update if new ATH is truly higher
          if (newATH > existingATH) {
            updateData.ath_price = newATH
            updateData.ath_timestamp = new Date().toISOString()
            updateData.ath_roi_percent = Math.max(0, ((newATH - priceAtCall) / priceAtCall) * 100)
            
            // Update ath_market_cap if we have total supply
            if (token.total_supply && newATH > 0) {
              updateData.ath_market_cap = newATH * token.total_supply
            }
            
            isNewATH = true
            
            console.log(`ATH Update for ${token.ticker}: ${existingATH} → ${newATH}`)

            // Track significant ATHs for notification
            // Requirements: min 250% ROI AND 20% increase from previous ATH
            const previousATH = token.ath_price || priceAtCall
            const athIncrease = ((newATH - previousATH) / previousATH) * 100
            
            if (updateData.ath_roi_percent >= 250 && athIncrease >= 20) {
              newATHs.push({
                ticker: token.ticker,
                network: token.network,
                poolAddress: token.pool_address,
                oldATH: previousATH,
                newATH: newATH,
                roi: updateData.ath_roi_percent.toFixed(2),
                volume24h: volume24h,
                liquidity: liquidityUsd
              })
              console.log(`ATH Alert queued: ${token.ticker} at ${updateData.ath_roi_percent.toFixed(2)}% ROI (${athIncrease.toFixed(1)}% increase from previous ATH)`)
            }
          }
        }
      }

      // Update database
      const { error: updateError } = await supabase
        .from('crypto_calls')
        .update(updateData)
        .eq('id', token.id)

      if (updateError) {
        console.error(`Failed to update token ${token.ticker}:`, updateError)
      } else {
        updated++
        if (isNewATH) {
          console.log(`New ATH for ${token.ticker}: $${currentPrice} (${updateData.ath_roi_percent?.toFixed(2)}% ROI)`)
        }
        // Token death tracking removed - only processing active tokens now
      }
    } catch (error) {
      console.error(`Error processing token ${token.ticker}:`, error)
    }
  }

  return { processed, updated }
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  const startTime = Date.now()
  
  try {
    // Note: DexScreener API returns max 30 pairs total, not 30 tokens
    // Using smaller batch size for better coverage
    // Processing only active (non-dead) tokens to avoid CPU limits
    const { batchSize = 20, delayMs = 50, maxTokens = 4000 } = await req.json().catch(() => ({}))
    
    // Initialize Supabase client with proper auth options for service role
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseKey, {
      auth: {
        persistSession: false,
        autoRefreshToken: false
      }
    })

    console.log(`Starting LOW-PRIORITY ultra-tracker processing (low liquidity tokens)...`)

    // Get all tokens with LOW liquidity ($1K-$20K) - these are less important to track
    // High liquidity tokens are handled by the main ultra-tracker
    const MIN_LIQUIDITY = 1000
    const MAX_LIQUIDITY = 20000
    
    let allTokens: any[] = []
    let offset = 0
    const pageSize = 1000
    
    while (allTokens.length < maxTokens) {
      const { data: batch, error: fetchError } = await supabase
        .from('crypto_calls')
        .select('id, ticker, network, contract_address, pool_address, price_at_call, current_price, ath_price, ath_timestamp, ath_roi_percent, volume_24h, liquidity_usd, price_change_24h, ath_last_checked, last_volume_check, price_updated_at, circulating_supply, total_supply, is_dead')
        .not('pool_address', 'is', null)
        .eq('is_invalidated', false)
        .neq('is_dead', true)  // Only process active tokens
        .gte('liquidity_usd', MIN_LIQUIDITY)  // Minimum $1K liquidity
        .lt('liquidity_usd', MAX_LIQUIDITY)    // Less than $20K liquidity
        .order('ath_last_checked', { ascending: true, nullsFirst: true })
        .range(offset, offset + pageSize - 1)
      
      if (fetchError) throw fetchError
      if (!batch || batch.length === 0) break
      
      allTokens = allTokens.concat(batch)
      if (batch.length < pageSize) break
      offset += pageSize
    }
    
    // Trim to maxTokens if we got more
    if (allTokens.length > maxTokens) {
      allTokens = allTokens.slice(0, maxTokens)
    }

    const tokens = allTokens
    
    if (!tokens || tokens.length === 0) {
      return new Response(JSON.stringify({ message: 'No tokens to process' }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      })
    }

    console.log(`Found ${tokens.length} low-liquidity tokens ($${MIN_LIQUIDITY.toLocaleString()}-$${MAX_LIQUIDITY.toLocaleString()}) to process`)

    // Group tokens by network for efficient API calls
    const tokensByNetwork: Record<string, typeof tokens> = {}
    tokens.forEach(token => {
      const network = token.network.toLowerCase()
      if (!tokensByNetwork[network]) {
        tokensByNetwork[network] = []
      }
      tokensByNetwork[network].push(token)
    })
    
    console.log(`Networks found: ${Object.keys(tokensByNetwork).join(', ')}`)

    let totalProcessed = 0
    let totalUpdated = 0
    const newATHs: any[] = []  // Shared array for ATH notifications
    const liquidityDeaths: any[] = []  // Tokens marked dead due to low liquidity
    const revivals: any[] = []  // Tokens revived due to liquidity recovery
    let apiCalls = 0
    const updatePromises: Promise<{ processed: number; updated: number }>[] = []

    // Process each network's tokens
    for (const [network, networkTokens] of Object.entries(tokensByNetwork)) {
      const dexScreenerNetwork = NETWORK_MAP[network]
      console.log(`Processing network: ${network} -> ${dexScreenerNetwork} (${networkTokens.length} tokens)`)
      if (!dexScreenerNetwork) {
        console.log(`Skipping unsupported network: ${network}`)
        continue
      }

      // Process in batches using pool addresses for better coverage
      for (let i = 0; i < networkTokens.length; i += batchSize) {
        const batch = networkTokens.slice(i, i + batchSize)
        const poolAddresses = batch.map(t => t.pool_address).join(',')
        
        try {
          // Minimal delay - DexScreener handles 300 req/min (5 per second)
          // With 50ms delay = 20 req/second, well within limits
          if (apiCalls > 0 && delayMs > 0) {
            await new Promise(resolve => setTimeout(resolve, delayMs))
          }
          
          // Use pairs endpoint with pool addresses for better coverage
          const apiUrl = `https://api.dexscreener.com/latest/dex/pairs/${dexScreenerNetwork}/${poolAddresses}`
          console.log(`API call ${++apiCalls}: Fetching ${batch.length} ${network} tokens via pool addresses`)
          
          const response = await fetch(apiUrl)
          if (!response.ok) {
            console.error(`DexScreener API error: ${response.status}`)
            continue
          }

          const data = await response.json()
          if (!data.pairs || !Array.isArray(data.pairs)) {
            console.log(`No pairs data for batch`)
            continue
          }

          // Process and update this batch in parallel (don't await)
          updatePromises.push(
            processAndUpdateBatch(data, batch, supabase, newATHs, liquidityDeaths, revivals)
          )

        } catch (error) {
          console.error(`Error fetching batch:`, error)
        }
      }
    }

    // Wait for all database updates to complete
    console.log(`Waiting for ${updatePromises.length} batch updates to complete...`)
    const results = await Promise.all(updatePromises)
    
    // Sum up the results
    for (const result of results) {
      totalProcessed += result.processed
      totalUpdated += result.updated
    }

    // Send Telegram notifications for significant new ATHs
    if (newATHs.length > 0) {
      const telegramBotToken = Deno.env.get('TELEGRAM_BOT_TOKEN_ATH')
      const telegramChatId = Deno.env.get('TELEGRAM_GROUP_ID_ATH')
      
      if (telegramBotToken && telegramChatId) {
        // Send notifications in parallel too
        const notificationPromises = newATHs.map(async (ath) => {
          const dexScreenerUrl = `https://dexscreener.com/${ath.network}/${ath.poolAddress}`
          const message = `🚀 *NEW ATH ALERT!*\n\n` +
            `Token: ${ath.ticker}\n` +
            `Network: ${ath.network}\n` +
            `New ATH: $${ath.newATH.toFixed(8)}\n` +
            `ROI: ${ath.roi}%\n` +
            `Volume 24h: $${(ath.volume24h / 1000).toFixed(1)}K\n` +
            `Liquidity: $${(ath.liquidity / 1000).toFixed(1)}K\n\n` +
            `[View on DexScreener](${dexScreenerUrl})`

          try {
            await fetch(`https://api.telegram.org/bot${telegramBotToken}/sendMessage`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                chat_id: telegramChatId,
                text: message,
                parse_mode: 'Markdown'
              })
            })
          } catch (error) {
            console.error('Failed to send Telegram notification:', error)
          }
        })

        await Promise.all(notificationPromises)
      }
    }

    const processingTime = Date.now() - startTime
    const result = {
      success: true,
      totalTokens: tokens.length,
      totalProcessed,
      totalUpdated,
      newATHs: newATHs.length,
      liquidityDeaths: liquidityDeaths.length,
      revivals: revivals.length,
      apiCalls,
      processingTimeMs: processingTime,
      tokensPerSecond: (totalProcessed / (processingTime / 1000)).toFixed(1),
      networksProcessed: Object.keys(tokensByNetwork).length
    }

    console.log(`Ultra-tracker completed:`, result)

    return new Response(JSON.stringify(result), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })
  } catch (error) {
    console.error('Error in ultra-tracker:', error)
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })
  }
})