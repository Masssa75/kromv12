import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.7';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

// Helper function to send Telegram message
async function sendTelegramMessage(botToken: string, chatId: string, message: string): Promise<any> {
  const telegramUrl = `https://api.telegram.org/bot${botToken}/sendMessage`;
  const telegramResponse = await fetch(telegramUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      chat_id: chatId,
      text: message,
      parse_mode: 'HTML',
      disable_web_page_preview: false,
    }),
  });

  const telegramResult = await telegramResponse.json();
  
  if (!telegramResponse.ok) {
    // If HTML parsing fails, try again without parsing
    if (telegramResult.description?.includes("can't parse entities")) {
      console.log(`HTML parsing failed, retrying as plain text...`);
      
      const plainResponse = await fetch(telegramUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          chat_id: chatId,
          text: message.replace(/<[^>]*>/g, ''), // Strip HTML tags
          disable_web_page_preview: false,
        }),
      });
      
      const plainResult = await plainResponse.json();
      
      if (!plainResponse.ok) {
        throw new Error(`Telegram API error (plain text): ${JSON.stringify(plainResult)}`);
      }
      
      return plainResult;
    } else {
      throw new Error(`Telegram API error: ${JSON.stringify(telegramResult)}`);
    }
  }

  return telegramResult;
}

// Format liquidity for display
function formatLiquidity(amount: number): string {
  if (amount >= 1000000) return `$${(amount / 1000000).toFixed(1)}M`;
  if (amount >= 1000) return `$${(amount / 1000).toFixed(0)}K`;
  return `$${amount.toFixed(0)}`;
}

// Helper to fetch token profile from DexScreener
async function fetchTokenProfile(contractAddress: string, network: string) {
  try {
    // Try token endpoint first (has website data)
    const tokenUrl = `https://api.dexscreener.com/latest/dex/tokens/${contractAddress}`;
    const response = await fetch(tokenUrl, {
      headers: {
        'Accept': 'application/json',
        'User-Agent': 'KROM Token Discovery Bot'
      }
    });

    if (response.ok) {
      const data = await response.json();
      
      // Find the pair for this network
      const pairs = data.pairs || [];
      const networkPair = pairs.find((p: any) => p.chainId === network) || pairs[0];
      
      if (networkPair?.info) {
        return {
          website: networkPair.info.websites?.[0]?.url || null,
          twitter: networkPair.info.socials?.find((s: any) => s.type === 'twitter')?.url || null,
          telegram: networkPair.info.socials?.find((s: any) => s.type === 'telegram')?.url || null,
          discord: networkPair.info.socials?.find((s: any) => s.type === 'discord')?.url || null,
        };
      }
    }
  } catch (error) {
    console.error(`Error fetching token profile for ${contractAddress}:`, error);
  }
  
  return null;
}

serve(async (req) => {
  // Handle CORS
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    // Initialize Supabase client with service role key
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey, {
      auth: {
        persistSession: false,
        autoRefreshToken: false
      }
    });

    console.log('🌐 Starting website checking for tokens...');

    // Get Telegram credentials (using ATH bot for token discovery too)
    const telegramBotToken = Deno.env.get('TELEGRAM_BOT_TOKEN_ATH') || Deno.env.get('TELEGRAM_BOT_TOKEN');
    const telegramChatId = Deno.env.get('TELEGRAM_GROUP_ID_ATH') || Deno.env.get('TELEGRAM_CHAT_ID');
    
    const hasTelegramConfig = telegramBotToken && telegramChatId;
    if (!hasTelegramConfig) {
      console.log('⚠️ Telegram credentials not configured - notifications disabled');
    }

    // Get tokens that are at least 1 hour old and haven't been checked
    const oneHourAgo = new Date(Date.now() - 60 * 60 * 1000).toISOString();
    
    const { data: tokensToCheck, error: fetchError } = await supabase
      .from('token_discovery')
      .select('id, contract_address, symbol, network, initial_liquidity_usd')
      .lte('first_seen_at', oneHourAgo)
      .is('website_checked_at', null)
      .limit(50); // Process 50 at a time to avoid timeouts

    if (fetchError) {
      throw fetchError;
    }

    console.log(`Found ${tokensToCheck?.length || 0} tokens to check for websites`);

    let websitesFound = 0;
    let tokensChecked = 0;
    let notificationsSent = 0;
    const errors: string[] = [];

    // Process each token
    for (const token of tokensToCheck || []) {
      try {
        console.log(`Checking ${token.symbol} (${token.network}): ${token.contract_address}`);
        
        // Fetch from DexScreener
        const socialData = await fetchTokenProfile(token.contract_address, token.network);
        
        // Update the database
        const updateData: any = {
          website_checked_at: new Date().toISOString()
        };
        
        let hasAnySocialData = false;
        const foundSocials: string[] = [];
        
        if (socialData) {
          if (socialData.website) {
            updateData.website_url = socialData.website;
            websitesFound++;
            hasAnySocialData = true;
            foundSocials.push(`🔗 Website: ${socialData.website}`);
            console.log(`  ✅ Website found: ${socialData.website}`);
          }
          if (socialData.twitter) {
            updateData.twitter_url = socialData.twitter;
            hasAnySocialData = true;
            foundSocials.push(`🐦 Twitter: ${socialData.twitter}`);
            console.log(`  🐦 Twitter found: ${socialData.twitter}`);
          }
          if (socialData.telegram) {
            updateData.telegram_url = socialData.telegram;
            hasAnySocialData = true;
            foundSocials.push(`💬 Telegram: ${socialData.telegram}`);
            console.log(`  💬 Telegram found: ${socialData.telegram}`);
          }
          if (socialData.discord) {
            updateData.discord_url = socialData.discord;
            hasAnySocialData = true;
            foundSocials.push(`💜 Discord: ${socialData.discord}`);
            console.log(`  💜 Discord found: ${socialData.discord}`);
          }
        } else {
          console.log(`  ⚠️ No social data found`);
        }
        
        const { error: updateError } = await supabase
          .from('token_discovery')
          .update(updateData)
          .eq('id', token.id);
        
        if (updateError) {
          errors.push(`Failed to update ${token.symbol}: ${updateError.message}`);
        } else {
          tokensChecked++;
          
          // Send Telegram notification if socials were found
          if (hasAnySocialData && hasTelegramConfig) {
            try {
              const networkDisplay = token.network.toUpperCase();
              const liquidity = formatLiquidity(token.initial_liquidity_usd || 0);
              
              const message = `🌐 <b>New Token with Website/Socials!</b>

<b>Token:</b> ${token.symbol} (${networkDisplay})
<b>Liquidity:</b> ${liquidity}

<b>Found:</b>
${foundSocials.join('\n')}

📊 <a href="https://dexscreener.com/${token.network === 'eth' ? 'ethereum' : token.network}/${token.contract_address}">View on DexScreener</a>`;
              
              await sendTelegramMessage(telegramBotToken!, telegramChatId!, message);
              console.log(`  📨 Telegram notification sent for ${token.symbol}`);
              notificationsSent++;
            } catch (notifyError) {
              console.error(`  ⚠️ Failed to send Telegram notification: ${notifyError}`);
              // Don't fail the whole process if notification fails
            }
          }
        }
        
        // Small delay to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 500));
        
      } catch (tokenError) {
        console.error(`Error processing ${token.symbol}:`, tokenError);
        errors.push(`Error processing ${token.symbol}: ${tokenError}`);
      }
    }

    // Summary
    const summary = {
      success: true,
      message: `Website checking completed`,
      stats: {
        tokens_checked: tokensChecked,
        websites_found: websitesFound,
        notifications_sent: notificationsSent,
        tokens_to_check: tokensToCheck?.length || 0,
        errors: errors.length
      },
      errors: errors.slice(0, 5), // Include first 5 errors if any
      timestamp: new Date().toISOString()
    };

    console.log('\n📊 Website Check Summary:', summary);

    return new Response(
      JSON.stringify(summary),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200 
      }
    );

  } catch (error) {
    console.error('❌ Fatal error in website checker:', error);
    
    return new Response(
      JSON.stringify({ 
        error: error.message,
        success: false 
      }),
      { 
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500
      }
    );
  }
});