import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

// Helper function to send Telegram message
async function sendTelegramMessage(botToken: string, chatId: number, message: string): Promise<any> {
  const telegramUrl = `https://api.telegram.org/bot${botToken}/sendMessage`
  const response = await fetch(telegramUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      chat_id: chatId,
      text: message,
      parse_mode: 'Markdown',
    }),
  })

  const result = await response.json()
  
  if (!response.ok) {
    throw new Error(`Telegram API error: ${JSON.stringify(result)}`)
  }

  return result
}

serve(async (req) => {
  try {
    // This endpoint handles both regular and premium bot webhooks
    const url = new URL(req.url)
    const isPremium = url.pathname.includes('premium')
    
    // Get the appropriate bot token
    const botToken = isPremium 
      ? Deno.env.get('TELEGRAM_BOT_TOKEN_PREMIUM')
      : Deno.env.get('TELEGRAM_BOT_TOKEN')
    
    if (!botToken) {
      throw new Error(`${isPremium ? 'Premium' : 'Regular'} bot token not configured`)
    }

    // Parse webhook update
    const update = await req.json()
    console.log('Received webhook update:', JSON.stringify(update))

    // Check if this is a message with text
    if (update.message && update.message.text) {
      const message = update.message
      const chatId = message.chat.id
      const text = message.text.trim()
      const chatType = message.chat.type
      const chatTitle = message.chat.title || 'Private Chat'

      // Handle /groupid command
      if (text === '/groupid' || text.startsWith('/groupid@')) {
        const responseText = `🆔 *Group Information*\n\n` +
          `*Chat ID:* \`${chatId}\`\n` +
          `*Chat Type:* ${chatType}\n` +
          `*Chat Title:* ${chatTitle}\n\n` +
          `_Use this ID in your Supabase environment variables._`

        await sendTelegramMessage(botToken, chatId, responseText)
        
        console.log(`Sent group ID ${chatId} to ${chatTitle}`)
      }
      // Handle /start command
      else if (text === '/start' || text.startsWith('/start@')) {
        const botType = isPremium ? 'Premium (SOLID/ALPHA only)' : 'Regular (all calls)'
        const responseText = `👋 *Welcome to KROM Notifier Bot!*\n\n` +
          `This is the *${botType}* notification bot.\n\n` +
          `Available commands:\n` +
          `• /groupid - Get this chat's ID\n` +
          `• /start - Show this help message`

        await sendTelegramMessage(botToken, chatId, responseText)
      }
    }

    // Return success response
    return new Response(
      JSON.stringify({ ok: true }),
      { headers: { "Content-Type": "application/json" } }
    )

  } catch (error) {
    console.error('Error in telegram-webhook:', error)
    return new Response(
      JSON.stringify({
        ok: false,
        error: error.message
      }),
      { 
        status: 200, // Return 200 to prevent Telegram from retrying
        headers: { "Content-Type": "application/json" }
      }
    )
  }
})