import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.38.4'
import { corsHeaders } from '../_shared/cors.ts'

// GeckoTerminal API configuration
const GECKO_API_BASE = 'https://api.geckoterminal.com/api/v2'
const COINGECKO_PRO_API_BASE = 'https://pro-api.coingecko.com/api/v3/onchain'
const NETWORK_MAP: Record<string, string> = {
  'ethereum': 'eth',
  'solana': 'solana',
  'bsc': 'bsc',
  'polygon': 'polygon',
  'arbitrum': 'arbitrum',
  'base': 'base',
  'hyperevm': 'hyperevm',
  'linea': 'linea',
  'abstract': 'abstract',
  'tron': 'tron',
  'sui': 'sui',
  'ton': 'ton'
}

Deno.serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders })
  }

  console.log('crypto-ath-verifier: Function started')

  try {
    const { limit = 10 } = await req.json().catch(() => ({}))
    console.log(`Processing limit: ${limit}`)
    
    // Initialize Supabase
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseKey, {
      auth: {
        persistSession: false,
        autoRefreshToken: false
      }
    })

    // Fetch tokens ordered by oldest verified first
    // Skip low liquidity tokens to avoid unreliable price data
    const { data: tokens, error: fetchError } = await supabase
      .from('crypto_calls')
      .select('id, ticker, network, contract_address, pool_address, buy_timestamp, price_at_call, ath_price, ath_timestamp, ath_roi_percent, ath_verified_at, raw_data, liquidity_usd')
      .not('pool_address', 'is', null)
      .not('price_at_call', 'is', null)
      .not('is_dead', 'is', true)
      .not('is_invalidated', 'is', true)
      .or('liquidity_usd.is.null,liquidity_usd.gte.15000') // Skip tokens with <$15K liquidity
      .order('ath_verified_at', { ascending: true, nullsFirst: true })
      .limit(limit)

    if (fetchError) {
      console.error('Database fetch error:', fetchError)
      throw fetchError
    }
    
    console.log(`Fetched ${tokens?.length || 0} tokens from database`)
    
    if (!tokens || tokens.length === 0) {
      return new Response(JSON.stringify({ 
        message: 'No tokens need ATH verification',
        processed: 0 
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    const results = []
    const errors = []
    let apiCallsUsed = 0

    for (const token of tokens) {
      try {
        // Get network name for GeckoTerminal
        const geckoNetwork = NETWORK_MAP[token.network]
        
        // Skip if network is not supported
        if (!geckoNetwork) {
          console.log(`⚠️ Skipping ${token.ticker} - unsupported network: ${token.network}`)
          errors.push({
            tokenId: token.id,
            ticker: token.ticker,
            error: `Unsupported network: ${token.network}`
          })
          continue
        }
        
        // Use buy_timestamp or fall back to raw_data timestamp
        const callTimestamp = token.buy_timestamp 
          ? new Date(token.buy_timestamp).getTime() / 1000
          : token.raw_data?.timestamp || 0
        
        if (!callTimestamp) {
          throw new Error(`No valid timestamp for token ${token.ticker}`)
        }

        console.log(`\nVerifying ${token.ticker} on ${geckoNetwork}`)
        console.log(`Call timestamp: ${new Date(callTimestamp * 1000).toISOString()}`)
        console.log(`Price at call: $${token.price_at_call}`)
        console.log(`Liquidity: ${token.liquidity_usd ? `$${token.liquidity_usd.toLocaleString()}` : 'Unknown'}`)
        
        // Get start of call day (midnight) to avoid missing intraday peaks
        const callDate = new Date(callTimestamp * 1000)
        callDate.setUTCHours(0, 0, 0, 0)
        const callDayStart = callDate.getTime() / 1000
        
        // Step 1: Get daily OHLCV data
        console.log(`Fetching daily OHLCV data...`)
        const dailyData = await fetchOHLCV(geckoNetwork, token.pool_address, 'day', 1000)
        apiCallsUsed++
        
        // Filter for data after token launch (from start of call day)
        const validDailyData = dailyData.filter((candle: any) => 
          candle.timestamp >= callDayStart && 
          candle.high > 0 && 
          candle.close > 0
        )
        
        if (validDailyData.length === 0) {
          throw new Error(`No valid daily data for ${token.ticker}`)
        }
        
        // Find the highest daily candle (use high to find the peak day)
        const highestDailyCandle = validDailyData.reduce((max: any, candle: any) => 
          candle.high > max.high ? candle : max
        )
        
        console.log(`Daily ATH: $${highestDailyCandle.high} on ${new Date(highestDailyCandle.timestamp * 1000).toISOString()}`)
        
        // Step 2: Get hourly data around the daily ATH
        console.log(`Fetching hourly OHLCV data...`)
        const beforeTs = highestDailyCandle.timestamp + (86400 + 43200) // 1.5 days after
        const hourlyData = await fetchOHLCV(
          geckoNetwork, 
          token.pool_address, 
          'hour', 
          72,
          beforeTs
        )
        apiCallsUsed++
        
        // Filter hourly data around the daily ATH (within 1 day)
        const hourlyAroundATH = hourlyData.filter((candle: any) => 
          Math.abs(candle.timestamp - highestDailyCandle.timestamp) <= 86400 && 
          candle.high > 0 &&
          candle.close > 0
        )
        
        // Find the highest hourly candle
        let highestHourlyCandle = highestDailyCandle
        if (hourlyAroundATH.length > 0) {
          highestHourlyCandle = hourlyAroundATH.reduce((max: any, candle: any) => 
            candle.high > max.high ? candle : max
          )
          console.log(`Hourly ATH: $${highestHourlyCandle.high} on ${new Date(highestHourlyCandle.timestamp * 1000).toISOString()}`)
        }
        
        // Step 3: Get minute data for precision
        console.log(`Fetching minute OHLCV data...`)
        const minuteBeforeTs = highestHourlyCandle.timestamp + 3600 // 1 hour after
        const minuteData = await fetchOHLCV(
          geckoNetwork, 
          token.pool_address, 
          'minute', 
          120,
          minuteBeforeTs
        )
        apiCallsUsed++
        
        // Filter minute data around the hourly ATH (within 1 hour) and after actual call time
        const minuteAroundATH = minuteData.filter((candle: any) => 
          Math.abs(candle.timestamp - highestHourlyCandle.timestamp) <= 3600 && 
          candle.timestamp >= callTimestamp && // Only consider minutes AFTER actual call time
          candle.high > 0 &&
          candle.close > 0
        )
        
        // Find the actual ATH from minute data
        let calculatedATH: number
        let athTimestamp: number
        
        if (minuteAroundATH.length > 0) {
          // Sort by high to find the peak candle
          const sortedByHigh = [...minuteAroundATH].sort((a: any, b: any) => b.high - a.high)
          const minuteATH = sortedByHigh[0]
          
          console.log(`Minute ATH candle: high=$${minuteATH.high}, open=$${minuteATH.open}, close=$${minuteATH.close}`)
          
          // Use the higher of open or close for more realistic ATH (filter out wicks)
          const bestPrice = Math.max(minuteATH.open, minuteATH.close)
          calculatedATH = bestPrice
          athTimestamp = minuteATH.timestamp
          
          console.log(`Using best price (max of open/close) as ATH: $${bestPrice} (wick high was $${minuteATH.high})`)
        } else {
          // Fall back to hourly data (use high from hourly)
          calculatedATH = highestHourlyCandle.high
          athTimestamp = highestHourlyCandle.timestamp
          console.log(`Using hourly ATH (no minute data): $${calculatedATH}`)
        }
        
        // Calculate ROI
        const calculatedROI = ((calculatedATH - token.price_at_call) / token.price_at_call) * 100
        
        const athResult = {
          ath_price: calculatedATH,
          ath_timestamp: athTimestamp,
          ath_roi_percent: Math.max(0, calculatedROI),
          ath_last_checked: new Date().toISOString()
        }

        // Check for discrepancy
        const discrepancyThreshold = 0.1 // 10% difference
        const storedATH = token.ath_price || 0
        
        let hasDiscrepancy = false
        let discrepancyType = ''
        
        if (storedATH > 0 && calculatedATH > 0) {
          const percentDifference = Math.abs(storedATH - calculatedATH) / Math.max(storedATH, calculatedATH)
          
          if (percentDifference > discrepancyThreshold) {
            hasDiscrepancy = true
            
            if (calculatedATH > storedATH) {
              discrepancyType = 'MISSED_ATH'
              console.log(`🚨 MISSED ATH for ${token.ticker}: Stored $${storedATH} but actual is $${calculatedATH}`)
            } else {
              discrepancyType = 'INFLATED_ATH'
              console.log(`⚠️ INFLATED ATH for ${token.ticker}: Stored $${storedATH} but actual is $${calculatedATH}`)
            }
            
            // Send notification for significant discrepancies
            // Higher threshold for low liquidity tokens to reduce noise
            const notificationThreshold = (token.liquidity_usd && token.liquidity_usd < 25000) ? 0.5 : 0.25
            if (percentDifference > notificationThreshold) { // >50% for low liquidity, >25% for others
              await sendDiscrepancyNotification(token, storedATH, calculatedATH, athResult.ath_roi_percent, discrepancyType, callTimestamp, token.liquidity_usd)
            }
          } else {
            console.log(`✅ ATH verified for ${token.ticker}: $${calculatedATH} (matches stored value)`)
          }
        } else if (!storedATH) {
          console.log(`📝 No stored ATH for ${token.ticker}. Setting to: $${calculatedATH}`)
          hasDiscrepancy = true
          discrepancyType = 'NO_ATH'
        }
        
        // Update database with verified ATH
        await updateToken(supabase, token.id, athResult, true)
        
        results.push({ 
          tokenId: token.id, 
          ticker: token.ticker, 
          ...athResult,
          hasDiscrepancy,
          discrepancyType,
          storedATH: token.ath_price,
          apiCallsUsed: 3
        })
        
        // Rate limiting
        await new Promise(resolve => setTimeout(resolve, 2000))

      } catch (error: any) {
        console.error(`Error processing ${token.ticker}:`, error)
        errors.push({
          tokenId: token.id,
          ticker: token.ticker,
          error: error.message || String(error)
        })
      }
    }

    const discrepanciesFound = results.filter((r: any) => r.hasDiscrepancy).length
    
    return new Response(JSON.stringify({
      message: 'ATH verification complete',
      processed: results.length,
      discrepanciesFound,
      errors: errors.length,
      totalApiCalls: apiCallsUsed,
      avgCallsPerToken: results.length > 0 ? (apiCallsUsed / results.length).toFixed(2) : 0,
      results: results.map((r: any) => ({
        ticker: r.ticker,
        ath_price: r.ath_price,
        ath_roi_percent: r.ath_roi_percent,
        hasDiscrepancy: r.hasDiscrepancy,
        discrepancyType: r.discrepancyType,
        storedATH: r.storedATH
      })),
      errors
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })

  } catch (error: any) {
    console.error('Error in crypto-ath-verifier:', error)
    return new Response(JSON.stringify({ 
      error: error.message || String(error)
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
})

async function fetchOHLCV(
  network: string, 
  poolAddress: string, 
  timeframe: 'day' | 'hour' | 'minute',
  limit: number = 1000,
  beforeTimestamp?: number
): Promise<any[]> {
  const apiKey = Deno.env.get('GECKO_TERMINAL_API_KEY')
  
  let url: URL
  let headers: Record<string, string> = {}
  
  if (apiKey && apiKey.startsWith('CG-')) {
    url = new URL(`${COINGECKO_PRO_API_BASE}/networks/${network}/pools/${poolAddress}/ohlcv/${timeframe}`)
    headers['x-cg-pro-api-key'] = apiKey
  } else {
    url = new URL(`${GECKO_API_BASE}/networks/${network}/pools/${poolAddress}/ohlcv/${timeframe}`)
  }
  
  url.searchParams.append('aggregate', '1')
  url.searchParams.append('limit', limit.toString())
  if (beforeTimestamp) {
    url.searchParams.append('before_timestamp', beforeTimestamp.toString())
  }

  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 30000)
    
    const response = await fetch(url.toString(), { 
      headers,
      signal: controller.signal 
    })
    
    clearTimeout(timeoutId)
    
    if (!response.ok) {
      const errorText = await response.text().catch(() => '')
      console.error(`GeckoTerminal API error ${response.status}: ${errorText}`)
      throw new Error(`GeckoTerminal API error: ${response.status}`)
    }

    const data = await response.json()
    const ohlcvList = data?.data?.attributes?.ohlcv_list || []
    
    return ohlcvList.map((candle: number[]) => ({
      timestamp: candle[0],
      open: candle[1] || 0,
      high: candle[2] || 0,
      low: candle[3] || 0,
      close: candle[4] || 0,
      volume: candle[5] || 0
    }))
  } catch (error: any) {
    if (error.name === 'AbortError') {
      console.error(`API request timed out for ${network}/${poolAddress}`)
      throw new Error(`API request timeout for ${network}/${poolAddress}`)
    }
    throw error
  }
}

async function updateToken(supabase: any, tokenId: string, athData: any, isVerification: boolean = false) {
  const updateData: any = {
    ath_price: athData.ath_price,
    ath_timestamp: new Date(athData.ath_timestamp * 1000).toISOString(),
    ath_roi_percent: athData.ath_roi_percent,
    ath_last_checked: athData.ath_last_checked
  }
  
  if (isVerification) {
    updateData.ath_verified_at = new Date().toISOString()
  }

  const { error } = await supabase
    .from('crypto_calls')
    .update(updateData)
    .eq('id', tokenId)

  if (error) throw error
}

async function sendDiscrepancyNotification(token: any, storedATH: number, calculatedATH: number, calculatedROI: number, discrepancyType: string, callTimestamp: number, liquidity?: number) {
  const telegramBotToken = Deno.env.get('TELEGRAM_BOT_TOKEN_ATH')
  const telegramChatId = Deno.env.get('TELEGRAM_GROUP_ID_ATH')
  
  if (!telegramBotToken || !telegramChatId) return
  
  const emoji = discrepancyType === 'MISSED_ATH' ? '🚨' : '⚠️'
  const percentDifference = Math.abs(storedATH - calculatedATH) / Math.max(storedATH, calculatedATH)
  
  // Create GeckoTerminal link
  const geckoNetwork = NETWORK_MAP[token.network] || token.network
  const geckoTerminalUrl = `https://www.geckoterminal.com/${geckoNetwork}/pools/${token.pool_address}`
  
  // Format call date/time
  const callDate = new Date(callTimestamp * 1000)
  const formattedCallDate = callDate.toLocaleString('en-US', { 
    month: 'short', 
    day: 'numeric', 
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
    timeZone: 'UTC'
  }) + ' UTC'
  
  const liquidityInfo = liquidity ? `Liquidity: $${liquidity.toLocaleString()}\n` : ''
  
  const message = `${emoji} *ATH VERIFICATION ALERT*\n\n` +
    `Token: ${token.ticker}\n` +
    `Network: ${token.network}\n` +
    `Type: ${discrepancyType.replace('_', ' ')}\n` +
    `Call Date: ${formattedCallDate}\n` +
    `${liquidityInfo}\n` +
    `Stored ATH: $${storedATH.toFixed(8)}\n` +
    `Actual ATH: $${calculatedATH.toFixed(8)}\n` +
    `Difference: ${calculatedATH > storedATH ? '+' : '-'}${(percentDifference * 100).toFixed(1)}%\n\n` +
    `Old ROI: ${token.ath_roi_percent?.toFixed(0)}%\n` +
    `Actual ROI: ${calculatedROI.toFixed(0)}%\n\n` +
    `[View on GeckoTerminal](${geckoTerminalUrl})\n\n` +
    `✅ ATH has been automatically corrected.`
  
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
  } catch (err) {
    console.error('Failed to send discrepancy notification:', err)
  }
}