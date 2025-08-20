import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.7'

// Helper function to determine the better tier
function getBetterTier(tier1: string, tier2: string): string {
  const tierRanking = { 'ALPHA': 4, 'SOLID': 3, 'BASIC': 2, 'TRASH': 1, 'UNKNOWN': 0 }
  const rank1 = tierRanking[tier1] || 0
  const rank2 = tierRanking[tier2] || 0
  return rank1 >= rank2 ? tier1 : tier2
}

// Helper function to check if a call qualifies for premium notifications
function isPremiumWorthy(claudeTier: string, xTier: string): boolean {
  const betterTier = getBetterTier(claudeTier, xTier)
  return betterTier === 'ALPHA' || betterTier === 'SOLID'
}

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
        .replace(/"/g, '') // Remove quotes from original message
      
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

serve(async (req) => {
  try {
    // Create Supabase client
    const supabase = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '',
      {
        auth: {
          persistSession: false,
          autoRefreshToken: false,
        },
      }
    )

    // Get Telegram credentials for both bots
    const telegramBotToken = Deno.env.get('TELEGRAM_BOT_TOKEN')
    const telegramGroupId = Deno.env.get('TELEGRAM_GROUP_ID')
    const premiumBotToken = Deno.env.get('TELEGRAM_BOT_TOKEN_PREMIUM')
    const premiumGroupId = Deno.env.get('TELEGRAM_GROUP_ID_PREMIUM')
    
    // SKIP REGULAR BOT - Only check premium bot credentials
    // if (!telegramBotToken || !telegramGroupId) {
    //   throw new Error('Regular Telegram credentials not configured')
    // }

    if (!premiumBotToken || !premiumGroupId) {
      throw new Error('Premium Telegram credentials not configured')
    }

    // Check total count of unnotified calls (regular bot) - exclude dead tokens
    const { count: totalUnnotified } = await supabase
      .from('crypto_calls')
      .select('*', { count: 'exact', head: true })
      .eq('notified', false)
      .not('analyzed_at', 'is', null)
      .or('is_dead.eq.false,is_dead.is.null')  // Skip dead tokens

    // Check total count of unnotified premium calls - exclude dead tokens
    const { count: totalUnnotifiedPremium } = await supabase
      .from('crypto_calls')
      .select('*', { count: 'exact', head: true })
      .eq('notified_premium', false)
      .not('analyzed_at', 'is', null)
      .or('is_dead.eq.false,is_dead.is.null')  // Skip dead tokens

    // SKIP REGULAR CALLS - Only fetch premium
    const limit = 10
    const unnotifiedCalls = [] // Skip regular calls
    const fetchError = null

    // Fetch unnotified premium calls - exclude dead tokens
    const { data: unnotifiedPremiumCalls, error: premiumFetchError } = await supabase
      .from('crypto_calls')
      .select('*')
      .eq('notified_premium', false)
      .not('analyzed_at', 'is', null)
      .or('is_dead.eq.false,is_dead.is.null')  // Skip dead tokens
      .order('buy_timestamp', { ascending: false })
      .limit(limit)

    if (fetchError) {
      throw fetchError
    }

    if (premiumFetchError) {
      throw premiumFetchError
    }

    console.log(`Found ${unnotifiedCalls?.length || 0} unnotified calls (Total: ${totalUnnotified})`)
    console.log(`Found ${unnotifiedPremiumCalls?.length || 0} unnotified premium calls (Total: ${totalUnnotifiedPremium})`)

    const regularNotificationsSent = []
    const premiumNotificationsSent = []
    const errors = []

    // Send overflow warning for regular bot if needed
    if (totalUnnotified && totalUnnotified > limit) {
      const warningMessage = `⚠️ *WARNING: Notification Queue Overflow*
      
There are *${totalUnnotified}* unnotified calls in the queue, but I'm limiting notifications to *${limit}* to prevent spam.

📊 *Backlog:* ${totalUnnotified - limit} calls will be processed in subsequent runs.

_This message was automatically generated to prevent notification flooding._`
      
      try {
        await sendTelegramMessage(telegramBotToken, telegramGroupId, warningMessage)
        console.log('Regular bot warning message sent successfully')
      } catch (e) {
        console.error('Error sending regular bot warning message:', e)
      }
    }

    // SKIP REGULAR NOTIFICATIONS - Only process premium
    /*
    // Process regular notifications
    for (const call of unnotifiedCalls || []) {
      try {
        // Extract relevant data
        const ticker = call.ticker || 'UNKNOWN'
        const buyTimestamp = call.buy_timestamp 
          ? new Date(call.buy_timestamp).toLocaleString('en-US', { timeZone: 'UTC' })
          : 'Unknown time'
        
        // Parse the raw_data for more details
        const rawData = call.raw_data
        const groupName = rawData.groupName || rawData.group?.name || 'Unknown Group'
        const tokenData = rawData.token || {}
        const tradeData = rawData.trade || {}
        
        // Get original message from raw data
        const originalMessage = rawData.message || rawData.content || rawData.text || ''
        
        // Get both tiers
        const claudeTier = call.analysis_tier || 'UNKNOWN'
        const xTier = call.x_analysis_tier || 'UNKNOWN'
        
        // Use the better tier for the header
        const betterTier = getBetterTier(claudeTier, xTier)
        
        // Get tier emoji and format header
        const tierHeader = {
          'ALPHA': '💎 NEW ALPHA CALL',
          'SOLID': '🟢 NEW SOLID CALL',
          'BASIC': '🟡 NEW BASIC CALL',
          'TRASH': '🔴 NEW TRASH CALL'
        }[betterTier] || '⚪ NEW CALL'

        // Format the message
        const message = `*${tierHeader}: ${ticker} on ${groupName}*

📊 *Analysis Ratings:*
• Call Quality: ${claudeTier} | X Research: ${xTier}${call.website_tier ? `\n• Website: ${call.website_tier} (${call.website_score}/21) - ${call.website_token_type || 'N/A'}` : ''}

📝 *Original Message:*
_"${originalMessage}"_

🐦 *X Summary:*
${call.x_analysis_summary || '• No X data available'}

📊 *Token:* ${ticker}
🏷️ *Group:* ${groupName}
🔗 *Network:* ${tokenData.network || 'Unknown'}
💵 *Contract:* \`${tokenData.ca || 'Unknown'}\`
🕐 *Buy Time:* ${buyTimestamp}
💰 *Buy Price:* ${tradeData.buyPrice || 'N/A'}
📈 *ROI:* ${tradeData.roi ? `${(tradeData.roi * 100 - 100).toFixed(2)}%` : 'N/A'}

[View on DexScreener](https://dexscreener.com/${tokenData.network || 'ethereum'}/${tokenData.ca || ''})
        `

        // Send regular bot notification
        const telegramResult = await sendTelegramMessage(telegramBotToken, telegramGroupId, message)

        // Mark as notified in database
        const { error: updateError } = await supabase
          .from('crypto_calls')
          .update({ notified: true })
          .eq('krom_id', call.krom_id)

        if (updateError) {
          throw updateError
        }

        regularNotificationsSent.push({
          krom_id: call.krom_id,
          ticker: ticker,
          telegram_message_id: telegramResult.result?.message_id
        })

        console.log(`Regular notification sent for ${ticker} (${call.krom_id})`)

      } catch (error) {
        console.error(`Error processing regular call ${call.krom_id}:`, error)
        errors.push({
          krom_id: call.krom_id,
          error: error.message,
          type: 'regular'
        })
      }
    }
    */

    // Process premium notifications (SOLID/ALPHA only)
    for (const call of unnotifiedPremiumCalls || []) {
      try {
        const claudeTier = call.analysis_tier || 'UNKNOWN'
        const xTier = call.x_analysis_tier || 'UNKNOWN'
        
        // Skip if not premium worthy
        if (!isPremiumWorthy(claudeTier, xTier)) {
          // Mark as notified_premium = true since we're "skipping" it
          await supabase
            .from('crypto_calls')
            .update({ notified_premium: true })
            .eq('krom_id', call.krom_id)
          continue
        }

        // Extract relevant data
        const ticker = call.ticker || 'UNKNOWN'
        const buyTimestamp = call.buy_timestamp 
          ? new Date(call.buy_timestamp).toLocaleString('en-US', { timeZone: 'UTC' })
          : 'Unknown time'
        
        // Parse the raw_data for more details
        const rawData = call.raw_data
        const groupName = rawData.groupName || rawData.group?.name || 'Unknown Group'
        const tokenData = rawData.token || {}
        const tradeData = rawData.trade || {}
        
        // Get original message from raw data
        const originalMessage = rawData.message || rawData.content || rawData.text || ''
        
        // Use the better tier for the header
        const betterTier = getBetterTier(claudeTier, xTier)
        
        // Get tier emoji and format header
        const tierHeader = {
          'ALPHA': '💎 NEW ALPHA CALL',
          'SOLID': '🟢 NEW SOLID CALL'
        }[betterTier] || '⚪ NEW CALL'

        // Format the message (same format as regular)
        const message = `*${tierHeader}: ${ticker} on ${groupName}*

📊 *Analysis Ratings:*
• Call Quality: ${claudeTier} | X Research: ${xTier}${call.website_tier ? `\n• Website: ${call.website_tier} (${call.website_score}/21) - ${call.website_token_type || 'N/A'}` : ''}

📝 *Original Message:*
_"${originalMessage}"_

🐦 *X Summary:*
${call.x_analysis_summary || '• No X data available'}

📊 *Token:* ${ticker}
🏷️ *Group:* ${groupName}
🔗 *Network:* ${tokenData.network || 'Unknown'}
💵 *Contract:* \`${tokenData.ca || 'Unknown'}\`
🕐 *Buy Time:* ${buyTimestamp}
💰 *Buy Price:* ${tradeData.buyPrice || 'N/A'}
📈 *ROI:* ${tradeData.roi ? `${(tradeData.roi * 100 - 100).toFixed(2)}%` : 'N/A'}

[View on DexScreener](https://dexscreener.com/${tokenData.network || 'ethereum'}/${tokenData.ca || ''})
        `

        // Send premium bot notification
        const premiumTelegramResult = await sendTelegramMessage(premiumBotToken, premiumGroupId, message)

        // Mark as notified_premium in database
        const { error: updateError } = await supabase
          .from('crypto_calls')
          .update({ notified_premium: true })
          .eq('krom_id', call.krom_id)

        if (updateError) {
          throw updateError
        }

        premiumNotificationsSent.push({
          krom_id: call.krom_id,
          ticker: ticker,
          tier: betterTier,
          telegram_message_id: premiumTelegramResult.result?.message_id
        })

        console.log(`Premium notification sent for ${ticker} (${call.krom_id}) - ${betterTier}`)

      } catch (error) {
        console.error(`Error processing premium call ${call.krom_id}:`, error)
        errors.push({
          krom_id: call.krom_id,
          error: error.message,
          type: 'premium'
        })
      }
    }

    return new Response(
      JSON.stringify({
        success: true,
        regularNotificationsSent: regularNotificationsSent.length,
        premiumNotificationsSent: premiumNotificationsSent.length,
        regularNotifications: regularNotificationsSent,
        premiumNotifications: premiumNotificationsSent,
        errors: errors.length > 0 ? errors : undefined
      }),
      { headers: { "Content-Type": "application/json" } }
    )

  } catch (error) {
    console.error('Error in crypto-notifier:', error)
    return new Response(
      JSON.stringify({
        success: false,
        error: error.message
      }),
      { 
        status: 500,
        headers: { "Content-Type": "application/json" }
      }
    )
  }
})