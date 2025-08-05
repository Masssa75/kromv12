import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.38.4'
import { corsHeaders } from '../_shared/cors.ts'

// Helper function to send Telegram message
async function sendTelegramMessage(botToken: string, groupId: string, message: string): Promise<any> {
  const telegramUrl = `https://api.telegram.org/bot${botToken}/sendMessage`
  const telegramResponse = await fetch(telegramUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      chat_id: groupId,
      text: message,
      parse_mode: 'Markdown',
      disable_web_page_preview: false,
    }),
  })

  const telegramResult = await telegramResponse.json()
  
  if (!telegramResponse.ok) {
    // If markdown parsing fails, try again without markdown
    if (telegramResult.description?.includes("can't parse entities")) {
      console.log(`Markdown parsing failed, retrying without markdown...`)
      
      // Create a plain text version of the message
      const plainMessage = message
        .replace(/\*/g, '')
        .replace(/_/g, '')
        .replace(/\`/g, '')
        .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
      
      const plainResponse = await fetch(telegramUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          chat_id: groupId,
          text: plainMessage,
          disable_web_page_preview: false,
        }),
      })
      
      const plainResult = await plainResponse.json()
      
      if (!plainResponse.ok) {
        throw new Error(`Telegram API error (plain text): ${JSON.stringify(plainResult)}`)
      }
      
      return plainResult
    } else {
      throw new Error(`Telegram API error: ${JSON.stringify(telegramResult)}`)
    }
  }

  return telegramResult
}

// Format percentage with color emoji
function formatPercentage(percent: number): string {
  if (percent >= 1000) return `🚀 +${percent.toFixed(0)}%` // 10x or more
  if (percent >= 500) return `💎 +${percent.toFixed(0)}%`  // 5x or more
  if (percent >= 200) return `🔥 +${percent.toFixed(0)}%`  // 2x or more
  if (percent >= 100) return `📈 +${percent.toFixed(0)}%`  // 100% or more
  return `📊 +${percent.toFixed(1)}%`
}

// Format price for display
function formatPrice(price: number): string {
  if (price >= 1) return `$${price.toFixed(2)}`
  if (price >= 0.01) return `$${price.toFixed(4)}`
  if (price >= 0.0001) return `$${price.toFixed(6)}`
  return `$${price.toExponential(4)}`
}

// Format time difference
function formatTimeSince(timestamp: string): string {
  const now = new Date()
  const then = new Date(timestamp)
  const diffMs = now.getTime() - then.getTime()
  const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
  const diffDays = Math.floor(diffHours / 24)
  
  if (diffDays > 0) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`
  if (diffHours > 0) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`
  const diffMinutes = Math.floor(diffMs / (1000 * 60))
  return `${diffMinutes} minute${diffMinutes > 1 ? 's' : ''} ago`
}

Deno.serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response(null, { headers: corsHeaders })
  }

  try {
    // Parse request body - expecting single token data
    const { tokenId, tokenData } = await req.json()
    
    if (!tokenId && !tokenData) {
      throw new Error('Either tokenId or tokenData must be provided')
    }
    
    // Initialize Supabase client
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
    const supabase = createClient(supabaseUrl, supabaseKey)

    // Get Telegram credentials for ATH bot
    const athBotToken = Deno.env.get('TELEGRAM_BOT_TOKEN_ATH')
    const athGroupId = Deno.env.get('TELEGRAM_GROUP_ID_ATH')
    
    if (!athBotToken || !athGroupId) {
      throw new Error('ATH Telegram credentials not configured')
    }

    let token = tokenData

    // If only tokenId provided, fetch the token data
    if (!token && tokenId) {
      const { data, error } = await supabase
        .from('crypto_calls')
        .select('*')
        .eq('id', tokenId)
        .single()
      
      if (error) throw error
      if (!data) throw new Error('Token not found')
      
      token = data
    }

    // Extract data for notification
    const ticker = token.ticker || 'UNKNOWN'
    const network = token.network || 'unknown'
    const contractAddress = token.contract_address
    const priceAtCall = token.price_at_call || 0
    const athPrice = token.ath_price || 0
    const athROI = token.ath_roi_percent || 0
    const athTimestamp = token.ath_timestamp
    const callTimestamp = token.buy_timestamp || token.created_at
    
    // Get group name from raw data
    const rawData = token.raw_data || {}
    const groupName = rawData.groupName || rawData.group?.name || rawData.callChannelName || 'Unknown Group'
    
    // Format the ATH notification message
    const message = `*🎯 NEW ALL-TIME HIGH ALERT!*

*${ticker}* just hit a new ATH ${formatPercentage(athROI)}

📊 *Performance:*
• Entry: ${formatPrice(priceAtCall)}
• ATH: ${formatPrice(athPrice)}
• Gain: ${formatPercentage(athROI)}

⏱️ *Timing:*
• Called: ${formatTimeSince(callTimestamp)}
• ATH reached: ${formatTimeSince(athTimestamp)}

📍 *Details:*
• Group: ${groupName}
• Network: ${network}${contractAddress ? `\n• Contract: \`${contractAddress}\`` : ''}
${contractAddress ? `\n[View on DexScreener](https://dexscreener.com/${network}/${contractAddress})` : ''}

_🔔 Set alerts to catch the next pump!_`

    // Send ATH notification
    const telegramResult = await sendTelegramMessage(athBotToken, athGroupId, message)

    console.log(`ATH notification sent for ${ticker} (+${athROI.toFixed(0)}%)`)

    return new Response(JSON.stringify({
      success: true,
      ticker: ticker,
      ath_roi: athROI,
      telegram_message_id: telegramResult.result?.message_id
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })

  } catch (error) {
    console.error('Error in crypto-ath-notifier:', error)
    return new Response(JSON.stringify({ 
      error: error.message 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    })
  }
})