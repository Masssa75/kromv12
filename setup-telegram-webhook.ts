// Setup script to configure Telegram webhook for your bots
// Run this locally with your bot token to set up the webhook

const PREMIUM_BOT_TOKEN = '7558329908:AAGPBE3MSAVYownFJq1eOouQmsQPNqU1yt0'
const SUPABASE_PROJECT_URL = 'https://eucfoommxxvqmmwdbkdv.supabase.co'

async function setWebhook(botToken: string, isPremium: boolean) {
  const botName = isPremium ? 'Premium Bot' : 'Regular Bot'
  const webhookPath = isPremium ? '/telegram-webhook/premium' : '/telegram-webhook'
  const webhookUrl = `${SUPABASE_PROJECT_URL}/functions/v1/telegram-webhook${isPremium ? '?premium=true' : ''}`
  
  console.log(`Setting up webhook for ${botName}...`)
  console.log(`Webhook URL: ${webhookUrl}`)
  
  // Set the webhook
  const setWebhookUrl = `https://api.telegram.org/bot${botToken}/setWebhook`
  const response = await fetch(setWebhookUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      url: webhookUrl,
      allowed_updates: ['message'], // Only receive message updates
    }),
  })
  
  const result = await response.json()
  
  if (result.ok) {
    console.log(`✅ ${botName} webhook set successfully!`)
    
    // Get webhook info to confirm
    const getWebhookUrl = `https://api.telegram.org/bot${botToken}/getWebhookInfo`
    const infoResponse = await fetch(getWebhookUrl)
    const info = await infoResponse.json()
    
    console.log(`Webhook info:`, info.result)
  } else {
    console.error(`❌ Failed to set ${botName} webhook:`, result)
  }
}

// For now, just set up the premium bot
// You can add the regular bot token here too if needed
async function main() {
  console.log('Setting up Telegram webhooks for KROM bots...\n')
  
  // Set up premium bot webhook
  await setWebhook(PREMIUM_BOT_TOKEN, true)
  
  console.log('\n✅ Setup complete!')
  console.log('\nNow you can use /groupid command in your Telegram groups!')
}

// Run the setup
main().catch(console.error)