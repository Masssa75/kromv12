import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.7'

// Helper function to determine the better tier
function getBetterTier(tier1: string, tier2: string): string {
  const tierRanking = { 'ALPHA': 4, 'SOLID': 3, 'BASIC': 2, 'TRASH': 1, 'UNKNOWN': 0 }
  const rank1 = tierRanking[tier1] || 0
  const rank2 = tierRanking[tier2] || 0
  return rank1 >= rank2 ? tier1 : tier2
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

    // Get Telegram credentials
    const telegramBotToken = Deno.env.get('TELEGRAM_BOT_TOKEN')
    const telegramGroupId = Deno.env.get('TELEGRAM_GROUP_ID')
    
    if (!telegramBotToken || !telegramGroupId) {
      throw new Error('Telegram credentials not configured')
    }

    // First, check total count of unnotified calls that have been analyzed
    const { count: totalUnnotified } = await supabase
      .from('crypto_calls')
      .select('*', { count: 'exact', head: true })
      .eq('notified', false)
      .not('analyzed_at', 'is', null)

    // Fetch calls that have been analyzed but not notified yet (limit to 10)
    const limit = 10
    const { data: unnotifiedCalls, error: fetchError } = await supabase
      .from('crypto_calls')
      .select('*')
      .eq('notified', false)
      .not('analyzed_at', 'is', null)
      .order('buy_timestamp', { ascending: false })
      .limit(limit)

    if (fetchError) {
      throw fetchError
    }

    console.log(`Found ${unnotifiedCalls?.length || 0} unnotified calls (Total unnotified: ${totalUnnotified})`)

    const notificationsSent = []
    const errors = []

    // If there are more unnotified calls than the limit, send a warning
    if (totalUnnotified && totalUnnotified > limit) {
      const warningMessage = `⚠️ *WARNING: Notification Queue Overflow*
      
There are *${totalUnnotified}* unnotified calls in the queue, but I'm limiting notifications to *${limit}* to prevent spam.

📊 *Backlog:* ${totalUnnotified - limit} calls will be processed in subsequent runs.

_This message was automatically generated to prevent notification flooding._`
      
      try {
        const response = await fetch(`https://api.telegram.org/bot${telegramBotToken}/sendMessage`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            chat_id: telegramGroupId,
            text: warningMessage,
            parse_mode: 'Markdown'
          })
        })

        if (!response.ok) {
          console.error(`Failed to send warning message: ${response.statusText}`)
        } else {
          console.log('Warning message sent successfully')
        }
      } catch (e) {
        console.error('Error sending warning message:', e)
      }
    }

    // Process each unnotified call
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
• Call Quality: ${claudeTier} | X Research: ${xTier}

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

        // Send Telegram notification
        const telegramUrl = `https://api.telegram.org/bot${telegramBotToken}/sendMessage`
        const telegramResponse = await fetch(telegramUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            chat_id: telegramGroupId,
            text: message,
            parse_mode: 'Markdown',
            disable_web_page_preview: false,
          }),
        })

        const telegramResult = await telegramResponse.json()
        
        if (!telegramResponse.ok) {
          // If markdown parsing fails, try again without markdown
          if (telegramResult.description?.includes("can't parse entities")) {
            console.log(`Markdown parsing failed for ${call.krom_id}, retrying without markdown...`)
            
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
                chat_id: telegramGroupId,
                text: plainMessage,
                disable_web_page_preview: false,
              }),
            })
            
            const plainResult = await plainResponse.json()
            
            if (!plainResponse.ok) {
              throw new Error(`Telegram API error (plain text): ${JSON.stringify(plainResult)}`)
            }
            
            // If plain text succeeded, continue with success flow
            // Update variables to use plain result
            Object.assign(telegramResult, plainResult)
          } else {
            throw new Error(`Telegram API error: ${JSON.stringify(telegramResult)}`)
          }
        }

        // Mark as notified in database
        const { error: updateError } = await supabase
          .from('crypto_calls')
          .update({ notified: true })
          .eq('krom_id', call.krom_id)

        if (updateError) {
          throw updateError
        }

        notificationsSent.push({
          krom_id: call.krom_id,
          ticker: ticker,
          telegram_message_id: telegramResult.result?.message_id
        })

        console.log(`Notification sent for ${ticker} (${call.krom_id})`)

      } catch (error) {
        console.error(`Error processing call ${call.krom_id}:`, error)
        errors.push({
          krom_id: call.krom_id,
          error: error.message
        })
      }
    }

    return new Response(
      JSON.stringify({
        success: true,
        notificationsSent: notificationsSent.length,
        notifications: notificationsSent,
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