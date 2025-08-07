import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.38.0'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface TokenVolume {
  contract_address: string
  volume_24h: number
  txns_24h: number
  liquidity_usd: number
  price_change_24h: number
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    const { limit = 100 } = await req.json()
    
    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseKey)

    console.log(`Starting volume check for up to ${limit} tokens...`)

    // Get tokens that need volume checking (oldest checked first)
    const { data: tokens, error: fetchError } = await supabase
      .from('crypto_calls')
      .select('id, ticker, network, contract_address, last_volume_check')
      .not('contract_address', 'is', null)
      .order('last_volume_check', { ascending: true, nullsFirst: true })
      .limit(limit)

    if (fetchError) throw fetchError
    if (!tokens || tokens.length === 0) {
      return new Response(JSON.stringify({ message: 'No tokens to check' }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      })
    }

    console.log(`Found ${tokens.length} tokens to check volume`)

    // Group tokens by network for efficient API calls
    const tokensByNetwork: Record<string, typeof tokens> = {}
    tokens.forEach(token => {
      const network = token.network.toLowerCase()
      if (!tokensByNetwork[network]) {
        tokensByNetwork[network] = []
      }
      tokensByNetwork[network].push(token)
    })

    // DexScreener network mapping
    const networkMap: Record<string, string> = {
      'ethereum': 'ethereum',
      'solana': 'solana',
      'bsc': 'bsc',
      'polygon': 'polygon',
      'arbitrum': 'arbitrum',
      'optimism': 'optimism',
      'avalanche': 'avalanche',
      'base': 'base'
    }

    let totalProcessed = 0
    let totalUpdated = 0

    // Process each network's tokens
    for (const [network, networkTokens] of Object.entries(tokensByNetwork)) {
      const dexScreenerNetwork = networkMap[network] || network
      
      // Process in batches of 30 (DexScreener limit)
      for (let i = 0; i < networkTokens.length; i += 30) {
        const batch = networkTokens.slice(i, i + 30)
        const addresses = batch.map(t => t.contract_address).join(',')
        
        try {
          // Call DexScreener API
          const response = await fetch(
            `https://api.dexscreener.com/tokens/v1/${dexScreenerNetwork}/${addresses}`,
            {
              headers: {
                'Accept': 'application/json',
                'User-Agent': 'KROM-Volume-Checker/1.0'
              }
            }
          )

          if (!response.ok) {
            console.error(`DexScreener API error: ${response.status} ${response.statusText}`)
            continue
          }

          const data = await response.json()
          const volumeMap: Record<string, TokenVolume> = {}

          // DexScreener returns an array of pairs directly
          if (Array.isArray(data)) {
            data.forEach((pair: any) => {
              const address = pair.baseToken?.address?.toLowerCase()
              if (!address) return

              const volume24h = parseFloat(pair.volume?.h24 || '0')
              const buys24h = parseInt(pair.txns?.h24?.buys || '0')
              const sells24h = parseInt(pair.txns?.h24?.sells || '0')
              const txns24h = buys24h + sells24h
              const liquidity = parseFloat(pair.liquidity?.usd || '0')
              const priceChange = parseFloat(pair.priceChange?.h24 || '0')

              // Use pair with highest liquidity for each token
              if (!volumeMap[address] || liquidity > volumeMap[address].liquidity_usd) {
                volumeMap[address] = {
                  contract_address: address,
                  volume_24h: volume24h,
                  txns_24h: txns24h,
                  liquidity_usd: liquidity,
                  price_change_24h: priceChange
                }
              }
            })
          }

          // Update database with volume data
          const updatePromises = batch.map(async (token) => {
            const volumeData = volumeMap[token.contract_address.toLowerCase()]
            
            if (volumeData) {
              const { error: updateError } = await supabase
                .from('crypto_calls')
                .update({
                  volume_24h: volumeData.volume_24h,
                  txns_24h: volumeData.txns_24h,
                  liquidity_usd: volumeData.liquidity_usd,
                  price_change_24h: volumeData.price_change_24h,
                  last_volume_check: new Date().toISOString()
                })
                .eq('id', token.id)

              if (!updateError) {
                totalUpdated++
                console.log(`Updated ${token.ticker}: $${volumeData.volume_24h.toFixed(2)} volume, $${volumeData.liquidity_usd.toFixed(2)} liquidity, ${volumeData.price_change_24h.toFixed(1)}% change`)
              }
            } else {
              // Mark as checked even if no data found
              await supabase
                .from('crypto_calls')
                .update({
                  volume_24h: 0,
                  txns_24h: 0,
                  last_volume_check: new Date().toISOString()
                })
                .eq('id', token.id)
            }
          })

          await Promise.all(updatePromises)
          totalProcessed += batch.length

          // Rate limiting: DexScreener allows 60 calls/minute for token endpoints
          // We're being conservative with 1 call per second
          await new Promise(resolve => setTimeout(resolve, 1000))

        } catch (error) {
          console.error(`Error processing batch for ${network}:`, error)
        }
      }
    }

    const result = {
      success: true,
      processed: totalProcessed,
      updated: totalUpdated,
      message: `Checked volume for ${totalProcessed} tokens, updated ${totalUpdated} with volume data`
    }

    console.log(result.message)

    return new Response(JSON.stringify(result), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })

  } catch (error) {
    console.error('Error in crypto-volume-checker:', error)
    return new Response(
      JSON.stringify({ error: error.message }),
      { 
        status: 500,
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      }
    )
  }
})