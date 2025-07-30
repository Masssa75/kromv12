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
  'base': 'base'
}

interface OHLCVCandle {
  timestamp: number
  open: number
  high: number
  low: number
  close: number
  volume?: number
}

interface ATHResult {
  ath_price: number
  ath_timestamp: number
  ath_roi_percent: number
  ath_close_price?: number  // For internal use only
}

Deno.serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders })
  }

  try {
    // Parse request body
    const { limit = 10 } = await req.json().catch(() => ({}))
    
    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseKey)

    // Fetch tokens that need ATH calculation
    const { data: tokens, error: fetchError } = await supabase
      .from('crypto_calls')
      .select('id, ticker, network, pool_address, buy_timestamp, price_at_call, raw_data')
      .not('pool_address', 'is', null)
      .not('price_at_call', 'is', null)
      .is('ath_price', null)  // Only tokens without ATH data
      .order('created_at', { ascending: true })
      .limit(limit)

    if (fetchError) throw fetchError
    if (!tokens || tokens.length === 0) {
      return new Response(JSON.stringify({ 
        message: 'No tokens need ATH calculation',
        processed: 0 
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    console.log(`Processing ${tokens.length} tokens for ATH calculation`)

    const results = []
    const errors = []

    for (const token of tokens) {
      try {
        // Get network name for GeckoTerminal
        const geckoNetwork = NETWORK_MAP[token.network] || token.network
        
        // Use buy_timestamp or fall back to raw_data timestamp
        const callTimestamp = token.buy_timestamp 
          ? new Date(token.buy_timestamp).getTime() / 1000
          : token.raw_data?.timestamp || 0
        
        if (!callTimestamp) {
          throw new Error(`No valid timestamp for token ${token.ticker}`)
        }

        console.log(`\nProcessing ${token.ticker} on ${geckoNetwork}`)
        console.log(`Call timestamp: ${new Date(callTimestamp * 1000).toISOString()}`)
        console.log(`Price at call: $${token.price_at_call}`)

        // TIER 1: Daily candles
        const dailyData = await fetchOHLCV(geckoNetwork, token.pool_address, 'day', 1000)
        const dailyAfterCall = dailyData
          .filter(candle => candle.timestamp >= callTimestamp && candle.high > 0)
          .sort((a, b) => b.high - a.high)

        if (dailyAfterCall.length === 0) {
          throw new Error('No price data after call date')
        }

        const dailyATH = dailyAfterCall[0]
        console.log(`Daily ATH: $${dailyATH.high} on ${new Date(dailyATH.timestamp * 1000).toISOString()}`)

        // TIER 2: Hourly candles around ATH day
        const beforeTs = dailyATH.timestamp + (86400 + 43200) // 1.5 days after
        const hourlyData = await fetchOHLCV(geckoNetwork, token.pool_address, 'hour', 72, beforeTs)
        
        const hourlyAroundATH = hourlyData
          .filter(candle => 
            Math.abs(candle.timestamp - dailyATH.timestamp) <= 86400 && 
            candle.high > 0
          )
          .sort((a, b) => b.high - a.high)

        if (hourlyAroundATH.length === 0) {
          // Fallback to daily data
          const dailyRoi = ((dailyATH.high - token.price_at_call) / token.price_at_call) * 100
          
          const athResult: ATHResult = {
            ath_price: dailyATH.high,
            ath_timestamp: dailyATH.timestamp,
            ath_roi_percent: Math.max(0, dailyRoi)  // Never negative
          }
          await updateToken(supabase, token.id, athResult)
          results.push({ tokenId: token.id, ticker: token.ticker, ...athResult })
          continue
        }

        const hourlyATH = hourlyAroundATH[0]
        console.log(`Hourly ATH: $${hourlyATH.high} at ${new Date(hourlyATH.timestamp * 1000).toISOString()}`)

        // TIER 3: Minute candles around ATH hour
        const minuteBeforeTs = hourlyATH.timestamp + 3600 // 1 hour after
        const minuteData = await fetchOHLCV(geckoNetwork, token.pool_address, 'minute', 120, minuteBeforeTs)
        
        const minuteAroundATH = minuteData
          .filter(candle => 
            Math.abs(candle.timestamp - hourlyATH.timestamp) <= 3600 && 
            candle.high > 0 &&
            candle.close > 0
          )
          .sort((a, b) => b.high - a.high)

        let athResult: ATHResult
        
        if (minuteAroundATH.length > 0) {
          const minuteATH = minuteAroundATH[0]
          console.log(`Minute ATH: $${minuteATH.high} (open: $${minuteATH.open}, close: $${minuteATH.close})`)
          
          // Use the higher of open or close for more realistic ATH
          const bestPrice = Math.max(minuteATH.open, minuteATH.close)
          const athRoi = ((bestPrice - token.price_at_call) / token.price_at_call) * 100
          
          athResult = {
            ath_price: bestPrice,  // Higher of open/close for realistic selling point
            ath_timestamp: minuteATH.timestamp,
            ath_roi_percent: Math.max(0, athRoi),  // Never negative - 0 means never exceeded entry
            ath_close_price: minuteATH.close  // Keep for logging
          }
          
          console.log(`Using best price (max of open/close) as ATH: $${bestPrice} (wick high was $${minuteATH.high})`)
        } else {
          // Fallback to hourly data
          const hourlyRoi = ((hourlyATH.high - token.price_at_call) / token.price_at_call) * 100
          
          athResult = {
            ath_price: hourlyATH.high,
            ath_timestamp: hourlyATH.timestamp,
            ath_roi_percent: Math.max(0, hourlyRoi)  // Never negative
          }
        }

        // Update database
        await updateToken(supabase, token.id, athResult)
        results.push({ tokenId: token.id, ticker: token.ticker, ...athResult })
        
        // Rate limiting - CoinGecko Pro API allows 500 calls/minute
        // We make 3 calls per token, so ~166 tokens per minute max
        // Using 0.5 second delay since we're on Pro API
        await new Promise(resolve => setTimeout(resolve, 500)) // 0.5 seconds between tokens

      } catch (error) {
        console.error(`Error processing ${token.ticker}:`, error)
        errors.push({
          tokenId: token.id,
          ticker: token.ticker,
          error: error.message
        })
      }
    }

    return new Response(JSON.stringify({
      message: 'ATH calculation complete',
      processed: results.length,
      errors: errors.length,
      results,
      errors
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })

  } catch (error) {
    console.error('Error in crypto-ath-historical:', error)
    return new Response(JSON.stringify({ 
      error: error.message 
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
): Promise<OHLCVCandle[]> {
  // Get API key from environment
  const apiKey = Deno.env.get('GECKO_TERMINAL_API_KEY')
  
  let url: URL
  let headers: Record<string, string> = {}
  
  if (apiKey && apiKey.startsWith('CG-')) {
    // Use CoinGecko Pro API for higher rate limits (500/min vs 30/min)
    url = new URL(`${COINGECKO_PRO_API_BASE}/networks/${network}/pools/${poolAddress}/ohlcv/${timeframe}`)
    headers['x-cg-pro-api-key'] = apiKey
  } else {
    // Fallback to public API
    url = new URL(`${GECKO_API_BASE}/networks/${network}/pools/${poolAddress}/ohlcv/${timeframe}`)
  }
  
  url.searchParams.append('aggregate', '1')
  url.searchParams.append('limit', limit.toString())
  if (beforeTimestamp) {
    url.searchParams.append('before_timestamp', beforeTimestamp.toString())
  }

  const response = await fetch(url.toString(), { headers })
  if (!response.ok) {
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
}

async function updateToken(supabase: any, tokenId: string, athData: ATHResult) {
  const updateData = {
    ath_price: athData.ath_price,
    ath_timestamp: new Date(athData.ath_timestamp * 1000).toISOString(),
    ath_roi_percent: athData.ath_roi_percent
  }

  const { error } = await supabase
    .from('crypto_calls')
    .update(updateData)
    .eq('id', tokenId)

  if (error) throw error
}