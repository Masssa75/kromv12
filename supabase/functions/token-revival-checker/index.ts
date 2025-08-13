import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.38.0'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  const startTime = Date.now()
  
  try {
    const { batchSize = 100, maxTokens = 1000 } = await req.json().catch(() => ({}))
    
    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseKey)

    console.log(`Starting token revival check...`)

    // Get dead tokens that haven't been checked recently
    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000).toISOString()
    
    const { data: tokens, error: fetchError } = await supabase
      .from('crypto_calls')
      .select('id, ticker, network, contract_address, pool_address, ath_last_checked')
      .not('pool_address', 'is', null)
      .eq('is_dead', true)  // Only check dead tokens
      .eq('is_invalidated', false)
      .or(`ath_last_checked.is.null,ath_last_checked.lt.${oneHourAgo}`)
      .order('ath_last_checked', { ascending: true, nullsFirst: true })
      .limit(maxTokens)
    
    if (fetchError) throw fetchError
    
    if (!tokens || tokens.length === 0) {
      return new Response(JSON.stringify({ 
        message: 'No dead tokens to check',
        totalChecked: 0,
        revivedCount: 0
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      })
    }

    console.log(`Found ${tokens.length} dead tokens to check`)

    let totalChecked = 0
    let revivedCount = 0
    const revivedTokens: string[] = []

    // Process in batches
    for (let i = 0; i < tokens.length; i += batchSize) {
      const batch = tokens.slice(i, i + batchSize)
      
      // Group by network for efficient checking
      const byNetwork: Record<string, typeof batch> = {}
      batch.forEach(token => {
        const network = token.network.toLowerCase()
        if (!byNetwork[network]) {
          byNetwork[network] = []
        }
        byNetwork[network].push(token)
      })

      // Check each network's tokens
      for (const [network, networkTokens] of Object.entries(byNetwork)) {
        // Use smaller batches for checking (10 at a time)
        for (let j = 0; j < networkTokens.length; j += 10) {
          const checkBatch = networkTokens.slice(j, j + 10)
          const poolAddresses = checkBatch.map(t => t.pool_address).join(',')
          
          try {
            // Check if these pools exist on DexScreener
            const url = `https://api.dexscreener.com/latest/dex/pairs/${network}/${poolAddresses}`
            const response = await fetch(url)
            
            if (response.ok) {
              const data = await response.json()
              const pairsArray = data.pairs || (data.pair ? [data.pair] : [])
              
              // Check which tokens are alive AND have sufficient liquidity
              for (const token of checkBatch) {
                totalChecked++
                
                const matchingPair = pairsArray.find((p: any) => 
                  p.pairAddress === token.pool_address
                )
                
                if (matchingPair) {
                  // Token exists on DexScreener - check liquidity
                  const liquidityUsd = matchingPair.liquidity?.usd || 0
                  const LIQUIDITY_THRESHOLD = 1000
                  
                  if (liquidityUsd >= LIQUIDITY_THRESHOLD) {
                    // Token has sufficient liquidity! Mark it as alive
                    await supabase
                      .from('crypto_calls')
                      .update({ 
                        is_dead: false,
                        liquidity_usd: liquidityUsd,
                        ath_last_checked: new Date().toISOString()
                      })
                      .eq('id', token.id)
                    
                    revivedCount++
                    revivedTokens.push(`${token.ticker} (${token.network}) - $${liquidityUsd.toFixed(2)}`)
                    console.log(`Token revived: ${token.ticker} on ${token.network} - Liquidity: $${liquidityUsd.toFixed(2)}`)
                  } else {
                    // Token exists but still has low liquidity
                    await supabase
                      .from('crypto_calls')
                      .update({ 
                        liquidity_usd: liquidityUsd,
                        ath_last_checked: new Date().toISOString()
                      })
                      .eq('id', token.id)
                    console.log(`Token ${token.ticker} still dead - Liquidity: $${liquidityUsd.toFixed(2)} < $${LIQUIDITY_THRESHOLD}`)
                  }
                } else {
                  // Still dead, just update check time
                  await supabase
                    .from('crypto_calls')
                    .update({ 
                      ath_last_checked: new Date().toISOString()
                    })
                    .eq('id', token.id)
                }
              }
            }
          } catch (error) {
            console.error(`Error checking batch:`, error)
          }
        }
      }
    }

    const processingTime = Date.now() - startTime
    const result = {
      success: true,
      totalChecked,
      revivedCount,
      revivedTokens: revivedTokens.slice(0, 10), // Show first 10
      processingTimeMs: processingTime,
      tokensPerSecond: (totalChecked / (processingTime / 1000)).toFixed(1)
    }

    console.log(`Completed: ${JSON.stringify(result)}`)

    // Send notification if tokens were revived
    if (revivedCount > 0) {
      const telegramBotToken = Deno.env.get('TELEGRAM_BOT_TOKEN_ATH')
      const telegramChatId = Deno.env.get('TELEGRAM_GROUP_ID_ATH')
      
      if (telegramBotToken && telegramChatId) {
        const message = `🔄 *TOKEN REVIVAL ALERT*\n\n` +
          `${revivedCount} tokens have sufficient liquidity (>$1000) again:\n` +
          revivedTokens.slice(0, 5).join('\n') +
          (revivedTokens.length > 5 ? `\n... and ${revivedTokens.length - 5} more` : '')

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
          console.error('Failed to send revival notification:', error)
        }
      }
    }

    return new Response(JSON.stringify(result), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })

  } catch (error) {
    console.error('Error in token-revival-checker:', error)
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    })
  }
})