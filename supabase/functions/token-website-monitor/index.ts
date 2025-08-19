import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.7';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

// Helper to send Telegram notifications
async function sendTelegramNotification(botToken: string, chatId: string, message: string) {
  try {
    const response = await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: chatId,
        text: message,
        parse_mode: 'HTML',
        disable_web_page_preview: false,
      }),
    });
    return response.ok;
  } catch (e) {
    console.error('Telegram notification failed:', e);
    return false;
  }
}

// Batch check tokens for websites
async function checkTokenBatch(addresses: string[]) {
  try {
    const addressList = addresses.join(',');
    const response = await fetch(
      `https://api.dexscreener.com/latest/dex/tokens/${addressList}`,
      { headers: { 'Accept': 'application/json' } }
    );
    
    if (!response.ok) return null;
    return await response.json();
  } catch (e) {
    console.error('DexScreener API error:', e);
    return null;
  }
}

// Calculate next check time based on age and check count
function calculateNextCheckTime(firstSeenAt: string, checkCount: number, hasHighLiquidity: boolean): Date | null {
  const now = new Date();
  const firstSeen = new Date(firstSeenAt);
  const ageHours = (now.getTime() - firstSeen.getTime()) / (1000 * 60 * 60);
  
  // Stop checking tokens older than 7 days or checked 8+ times
  if (ageHours > 168 || checkCount >= 8) {
    return null; // No more checks needed
  }
  
  // Define check intervals based on token age and liquidity
  let intervalMinutes: number;
  
  if (hasHighLiquidity) {
    // High liquidity tokens (>$50K) - check more frequently
    if (checkCount === 0) intervalMinutes = 15;        // First check after 15 minutes
    else if (checkCount === 1) intervalMinutes = 30;   // Second check after 30 minutes
    else if (checkCount === 2) intervalMinutes = 60;   // Third check after 1 hour
    else if (checkCount === 3) intervalMinutes = 120;  // Fourth check after 2 hours
    else if (checkCount === 4) intervalMinutes = 240;  // Fifth check after 4 hours
    else if (checkCount === 5) intervalMinutes = 480;  // Sixth check after 8 hours
    else if (checkCount === 6) intervalMinutes = 720;  // Seventh check after 12 hours
    else intervalMinutes = 1440;                       // Final check after 24 hours
  } else {
    // Normal/low liquidity tokens - less frequent checks
    if (checkCount === 0) intervalMinutes = 60;        // First check after 1 hour
    else if (checkCount === 1) intervalMinutes = 240;  // Second check after 4 hours
    else if (checkCount === 2) intervalMinutes = 720;  // Third check after 12 hours
    else if (checkCount === 3) intervalMinutes = 1440; // Fourth check after 24 hours
    else if (checkCount === 4) intervalMinutes = 2880; // Fifth check after 48 hours
    else intervalMinutes = 4320;                       // Final checks after 72 hours
  }
  
  return new Date(now.getTime() + intervalMinutes * 60 * 1000);
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    // Initialize Supabase
    const supabaseUrl = Deno.env.get('SUPABASE_URL')!;
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!;
    const supabase = createClient(supabaseUrl, supabaseKey, {
      auth: { persistSession: false, autoRefreshToken: false }
    });

    // Get Telegram credentials
    const telegramBotToken = Deno.env.get('TELEGRAM_BOT_TOKEN_ATH') || Deno.env.get('TELEGRAM_BOT_TOKEN');
    const telegramChatId = Deno.env.get('TELEGRAM_GROUP_ID_ATH') || Deno.env.get('TELEGRAM_CHAT_ID');
    
    console.log('🔍 Starting smart website monitoring...');

    let totalChecked = 0;
    let newWebsitesFound = 0;
    const notifications: string[] = [];
    const stats = {
      neverChecked: 0,
      scheduled: 0,
      websites: 0,
      timingData: [] as any[]
    };

    // Priority 1: Never checked tokens (highest priority)
    console.log('\n📊 Priority 1: Never checked tokens');
    const { data: neverChecked, error: error1 } = await supabase
      .from('token_discovery')
      .select('id, contract_address, symbol, network, initial_liquidity_usd, first_seen_at')
      .is('website_checked_at', null)
      .is('website_url', null)
      .order('initial_liquidity_usd', { ascending: false, nullsFirst: false })
      .limit(60); // Process more in each run

    if (neverChecked && neverChecked.length > 0) {
      console.log(`  Found ${neverChecked.length} never-checked tokens`);
      stats.neverChecked = neverChecked.length;
      
      // Process in batches of 30
      for (let i = 0; i < neverChecked.length; i += 30) {
        const batch = neverChecked.slice(i, i + 30);
        const addresses = batch.map(t => t.contract_address);
        
        const data = await checkTokenBatch(addresses);
        if (!data) continue;

        // Process results
        for (const token of batch) {
          const pairs = data.pairs?.filter(
            (p: any) => p.baseToken?.address?.toLowerCase() === token.contract_address.toLowerCase()
          ) || [];

          let websiteFound = false;
          const now = new Date();
          const updateData: any = { 
            website_checked_at: now.toISOString(),
            last_check_at: now.toISOString(),
            website_check_count: 1
          };

          for (const pair of pairs) {
            const info = pair.info;
            if (!info) continue;

            // Extract social data
            const websites = info.websites || [];
            const socials = info.socials || [];

            if (websites.length > 0 && !updateData.website_url) {
              updateData.website_url = websites[0].url;
              updateData.website_found_at = now.toISOString();
              websiteFound = true;
              newWebsitesFound++;
              
              // Calculate time to add website
              const ageHours = (now.getTime() - new Date(token.first_seen_at).getTime()) / (1000 * 60 * 60);
              console.log(`  ✅ ${token.symbol}: Website found after ${ageHours.toFixed(1)}h!`);
              
              stats.timingData.push({
                symbol: token.symbol,
                network: token.network,
                liquidity: token.initial_liquidity_usd,
                hoursToWebsite: ageHours
              });
            }

            for (const social of socials) {
              if (social.type === 'twitter' && !updateData.twitter_url) {
                updateData.twitter_url = social.url;
              } else if (social.type === 'telegram' && !updateData.telegram_url) {
                updateData.telegram_url = social.url;
              } else if (social.type === 'discord' && !updateData.discord_url) {
                updateData.discord_url = social.url;
              }
            }

            if (websiteFound || updateData.twitter_url || updateData.telegram_url) {
              break; // Found social data
            }
          }

          // Calculate next check time if no website found
          if (!websiteFound) {
            const hasHighLiquidity = (token.initial_liquidity_usd || 0) > 50000;
            updateData.next_check_at = calculateNextCheckTime(
              token.first_seen_at, 
              1, 
              hasHighLiquidity
            );
          } else {
            // Website found, no more checks needed
            updateData.next_check_at = null;
          }

          // Update database
          await supabase
            .from('token_discovery')
            .update(updateData)
            .eq('id', token.id);

          totalChecked++;

          // Send notification if website found and Telegram configured
          if (websiteFound && telegramBotToken && telegramChatId) {
            const liquidity = new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: 'USD',
              minimumFractionDigits: 0,
              maximumFractionDigits: 0,
            }).format(token.initial_liquidity_usd || 0);
            
            const ageHours = (now.getTime() - new Date(token.first_seen_at).getTime()) / (1000 * 60 * 60);

            const message = `🌐 <b>Token Website Discovered!</b>

<b>${token.symbol}</b> (${token.network.toUpperCase()})
Liquidity: ${liquidity}
Website added after: ${ageHours.toFixed(1)} hours
Website: ${updateData.website_url}

<a href="https://dexscreener.com/${token.network === 'eth' ? 'ethereum' : token.network}/${token.contract_address}">View on DexScreener</a>`;

            const sent = await sendTelegramNotification(telegramBotToken, telegramChatId, message);
            if (sent) notifications.push(token.symbol);
          }
        }
      }
    } else {
      console.log(`  No never-checked tokens found`);
    }

    // Priority 2: Scheduled rechecks (tokens due for another check)
    console.log('\n📊 Priority 2: Scheduled rechecks');
    const now = new Date();
    const { data: scheduledTokens, error: error2 } = await supabase
      .from('token_discovery')
      .select('id, contract_address, symbol, network, initial_liquidity_usd, first_seen_at, website_check_count')
      .is('website_url', null)
      .not('next_check_at', 'is', null)
      .lte('next_check_at', now.toISOString())
      .order('next_check_at', { ascending: true })
      .limit(30);

    if (scheduledTokens && scheduledTokens.length > 0) {
      console.log(`  Found ${scheduledTokens.length} tokens scheduled for recheck`);
      stats.scheduled = scheduledTokens.length;
      
      // Process in batches of 30
      for (let i = 0; i < scheduledTokens.length; i += 30) {
        const batch = scheduledTokens.slice(i, i + 30);
        const addresses = batch.map(t => t.contract_address);
        
        const data = await checkTokenBatch(addresses);
        if (!data) continue;

        // Process results
        for (const token of batch) {
          const pairs = data.pairs?.filter(
            (p: any) => p.baseToken?.address?.toLowerCase() === token.contract_address.toLowerCase()
          ) || [];

          let websiteFound = false;
          const checkTime = new Date();
          const newCheckCount = (token.website_check_count || 0) + 1;
          const updateData: any = { 
            last_check_at: checkTime.toISOString(),
            website_check_count: newCheckCount
          };

          for (const pair of pairs) {
            const info = pair.info;
            if (!info) continue;

            // Extract social data
            const websites = info.websites || [];
            const socials = info.socials || [];

            if (websites.length > 0 && !updateData.website_url) {
              updateData.website_url = websites[0].url;
              updateData.website_found_at = checkTime.toISOString();
              websiteFound = true;
              newWebsitesFound++;
              
              // Calculate time to add website
              const ageHours = (checkTime.getTime() - new Date(token.first_seen_at).getTime()) / (1000 * 60 * 60);
              console.log(`  ✅ ${token.symbol}: Website found after ${ageHours.toFixed(1)}h (check #${newCheckCount})!`);
              
              stats.timingData.push({
                symbol: token.symbol,
                network: token.network,
                liquidity: token.initial_liquidity_usd,
                hoursToWebsite: ageHours,
                checksBeforeFound: newCheckCount
              });
            }

            for (const social of socials) {
              if (social.type === 'twitter' && !updateData.twitter_url) {
                updateData.twitter_url = social.url;
              } else if (social.type === 'telegram' && !updateData.telegram_url) {
                updateData.telegram_url = social.url;
              } else if (social.type === 'discord' && !updateData.discord_url) {
                updateData.discord_url = social.url;
              }
            }

            if (websiteFound || updateData.twitter_url || updateData.telegram_url) {
              break; // Found social data
            }
          }

          // Calculate next check time if no website found
          if (!websiteFound) {
            const hasHighLiquidity = (token.initial_liquidity_usd || 0) > 50000;
            updateData.next_check_at = calculateNextCheckTime(
              token.first_seen_at, 
              newCheckCount, 
              hasHighLiquidity
            );
            
            if (updateData.next_check_at) {
              console.log(`  ⏰ ${token.symbol}: Scheduled for check #${newCheckCount + 1} at ${updateData.next_check_at.toISOString()}`);
            } else {
              console.log(`  ⛔ ${token.symbol}: Max checks reached (${newCheckCount}), stopping`);
            }
          } else {
            // Website found, no more checks needed
            updateData.next_check_at = null;
          }

          // Update database
          await supabase
            .from('token_discovery')
            .update(updateData)
            .eq('id', token.id);

          totalChecked++;

          // Send notification if website found
          if (websiteFound && telegramBotToken && telegramChatId) {
            const liquidity = new Intl.NumberFormat('en-US', {
              style: 'currency',
              currency: 'USD',
              minimumFractionDigits: 0,
              maximumFractionDigits: 0,
            }).format(token.initial_liquidity_usd || 0);
            
            const ageHours = (checkTime.getTime() - new Date(token.first_seen_at).getTime()) / (1000 * 60 * 60);

            const message = `🌐 <b>Token Website Discovered!</b>

<b>${token.symbol}</b> (${token.network.toUpperCase()})
Liquidity: ${liquidity}
Website added after: ${ageHours.toFixed(1)} hours
Discovery on check #${newCheckCount}
Website: ${updateData.website_url}

<a href="https://dexscreener.com/${token.network === 'eth' ? 'ethereum' : token.network}/${token.contract_address}">View on DexScreener</a>`;

            const sent = await sendTelegramNotification(telegramBotToken, telegramChatId, message);
            if (sent) notifications.push(token.symbol);
          }
        }
      }
    } else {
      console.log(`  No tokens scheduled for recheck`);
    }

    // Generate statistics summary
    console.log(`\n📊 Website Discovery Statistics:`);
    if (stats.timingData.length > 0) {
      const avgHours = stats.timingData.reduce((sum, t) => sum + t.hoursToWebsite, 0) / stats.timingData.length;
      const minHours = Math.min(...stats.timingData.map(t => t.hoursToWebsite));
      const maxHours = Math.max(...stats.timingData.map(t => t.hoursToWebsite));
      
      console.log(`  Websites discovered: ${stats.timingData.length}`);
      console.log(`  Average time to website: ${avgHours.toFixed(1)} hours`);
      console.log(`  Fastest: ${minHours.toFixed(1)} hours`);
      console.log(`  Slowest: ${maxHours.toFixed(1)} hours`);
    }

    console.log(`\n✅ Smart website monitoring completed:`);
    console.log(`  Total checked: ${totalChecked}`);
    console.log(`  New websites found: ${newWebsitesFound}`);
    console.log(`  Never-checked processed: ${stats.neverChecked}`);
    console.log(`  Scheduled rechecks: ${stats.scheduled}`);

    return new Response(JSON.stringify({
      success: true,
      checked: totalChecked,
      websites_found: newWebsitesFound,
      notifications_sent: notifications.length,
      stats: {
        never_checked: stats.neverChecked,
        scheduled_rechecks: stats.scheduled,
        timing_data: stats.timingData
      },
      timestamp: new Date().toISOString(),
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error) {
    console.error('Error in website monitor:', error);
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});