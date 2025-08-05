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
  ath_last_checked: string
}

Deno.serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders })
  }

  try {
    // Parse request body
    const { limit = 25 } = await req.json().catch(() => ({}))
    
    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseKey)

    // Fetch tokens ordered by oldest checked first
    const { data: tokens, error: fetchError } = await supabase
      .from('crypto_calls')
      .select('id, ticker, network, pool_address, buy_timestamp, price_at_call, ath_price, ath_timestamp, ath_roi_percent, ath_last_checked, raw_data')
      .not('pool_address', 'is', null)
      .not('price_at_call', 'is', null)
      .not('is_dead', 'is', true)
      .order('ath_last_checked', { ascending: true, nullsFirst: true })
      .limit(limit)

    if (fetchError) throw fetchError
    if (!tokens || tokens.length === 0) {
      return new Response(JSON.stringify({ 
        message: 'No tokens need ATH updates',
        processed: 0 
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      })
    }

    console.log(`Processing ${tokens.length} tokens for ATH updates`)

    const results = []
    const errors = []
    let apiCallsUsed = 0

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
        
        let athResult: ATHResult

        // Check if token already has ATH data
        if (token.ath_price && token.ath_timestamp) {
          // Optimized path: Only check since last update
          const lastChecked = token.ath_last_checked 
            ? new Date(token.ath_last_checked).getTime() / 1000
            : new Date(token.ath_timestamp).getTime() / 1000
          
          const hoursSinceCheck = Math.ceil((Date.now() / 1000 - lastChecked) / 3600)
          
          console.log(`Token has ATH. Checking ${hoursSinceCheck} hours since last check`)
          
          // Single API call for hourly data since last check
          const hourlyData = await fetchOHLCV(
            geckoNetwork, 
            token.pool_address, 
            'hour', 
            Math.min(hoursSinceCheck + 24, 1000) // Add 24h buffer, max 1000
          )
          apiCallsUsed++
          
          // Find if there's a new high
          const newHighCandle = hourlyData.find(candle => 
            candle.high > token.ath_price && candle.timestamp >= callTimestamp
          )
          
          if (newHighCandle) {
            console.log(`New ATH found! Previous: $${token.ath_price}, New high: $${newHighCandle.high}`)
            
            // Get minute precision for the new ATH hour
            const minuteBeforeTs = newHighCandle.timestamp + 3600
            const minuteData = await fetchOHLCV(
              geckoNetwork, 
              token.pool_address, 
              'minute', 
              120, 
              minuteBeforeTs
            )
            apiCallsUsed++
            
            const minuteAroundATH = minuteData
              .filter(candle => 
                Math.abs(candle.timestamp - newHighCandle.timestamp) <= 3600 &&
                candle.timestamp >= callTimestamp &&
                candle.high > 0 &&
                candle.close > 0
              )
              .sort((a, b) => b.high - a.high)
            
            if (minuteAroundATH.length > 0) {
              const minuteATH = minuteAroundATH[0]
              const bestPrice = Math.max(minuteATH.open, minuteATH.close)
              const athRoi = ((bestPrice - token.price_at_call) / token.price_at_call) * 100
              
              athResult = {
                ath_price: bestPrice,
                ath_timestamp: minuteATH.timestamp,
                ath_roi_percent: Math.max(0, athRoi),
                ath_last_checked: new Date().toISOString()
              }
              
              // Send notification if this is a new ATH with significant gain
              if (athRoi > 10) { // Only notify if > 10% gain
                console.log(`New ATH detected for ${token.ticker}: +${athRoi.toFixed(0)}%, sending notification...`)
                
                // Fire and forget - don't wait for notification response
                fetch('https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-ath-notifier', {
                  method: 'POST',
                  headers: {
                    'Authorization': 'Bearer ' + Deno.env.get('SUPABASE_ANON_KEY'),
                    'Content-Type': 'application/json'
                  },
                  body: JSON.stringify({
                    tokenData: {
                      ...token,
                      ath_price: bestPrice,
                      ath_timestamp: new Date(minuteATH.timestamp * 1000).toISOString(),
                      ath_roi_percent: Math.max(0, athRoi)
                    }
                  })
                }).catch(err => console.error('Notification failed:', err))
              }
            } else {
              // Use hourly data
              const athRoi = ((newHighCandle.high - token.price_at_call) / token.price_at_call) * 100
              
              athResult = {
                ath_price: newHighCandle.high,
                ath_timestamp: newHighCandle.timestamp,
                ath_roi_percent: Math.max(0, athRoi),
                ath_last_checked: new Date().toISOString()
              }
              
              // Send notification if this is a new ATH with significant gain
              if (athRoi > 10) { // Only notify if > 10% gain
                console.log(`New ATH detected for ${token.ticker}: +${athRoi.toFixed(0)}%, sending notification...`)
                
                // Fire and forget - don't wait for notification response
                fetch('https://eucfoommxxvqmmwdbkdv.supabase.co/functions/v1/crypto-ath-notifier', {
                  method: 'POST',
                  headers: {
                    'Authorization': 'Bearer ' + Deno.env.get('SUPABASE_ANON_KEY'),
                    'Content-Type': 'application/json'
                  },
                  body: JSON.stringify({
                    tokenData: {
                      ...token,
                      ath_price: newHighCandle.high,
                      ath_timestamp: new Date(newHighCandle.timestamp * 1000).toISOString(),
                      ath_roi_percent: Math.max(0, athRoi)
                    }
                  })
                }).catch(err => console.error('Notification failed:', err))
              }
            }
          } else {
            // No new ATH, just update last checked
            console.log(`No new ATH. Current ATH remains at $${token.ath_price}`)
            athResult = {
              ath_price: token.ath_price,
              ath_timestamp: new Date(token.ath_timestamp).getTime() / 1000,
              ath_roi_percent: token.ath_roi_percent,
              ath_last_checked: new Date().toISOString()
            }
          }
        } else {
          // No ATH data - do full calculation (fallback to historical function logic)
          console.log(`No ATH data. Performing full calculation`)
          
          // This shouldn't happen often as crypto-ath-historical handles these
          // But included for completeness
          throw new Error('Token missing ATH data - use crypto-ath-historical function')
        }

        // Update database
        await updateToken(supabase, token.id, athResult)
        results.push({ 
          tokenId: token.id, 
          ticker: token.ticker, 
          ...athResult,
          apiCallsUsed: athResult.ath_price !== token.ath_price ? 2 : 1
        })
        
        // Rate limiting - Using free tier (30 calls/minute)
        // We process up to 25 tokens/minute with avg 1.2 calls each
        await new Promise(resolve => setTimeout(resolve, 500)) // 0.5 second between tokens

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
      message: 'ATH update complete',
      processed: results.length,
      errors: errors.length,
      totalApiCalls: apiCallsUsed,
      avgCallsPerToken: (apiCallsUsed / results.length).toFixed(2),
      results,
      errors
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })

  } catch (error) {
    console.error('Error in crypto-ath-update:', error)
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
    // Use free GeckoTerminal API
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
    ath_roi_percent: athData.ath_roi_percent,
    ath_last_checked: athData.ath_last_checked
  }

  const { error } = await supabase
    .from('crypto_calls')
    .update(updateData)
    .eq('id', tokenId)

  if (error) throw error
}