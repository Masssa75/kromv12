import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.7';

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
};

// Constants
const SCRAPERAPI_KEY = Deno.env.get('SCRAPERAPI_KEY') || '';
const OPENROUTER_API_KEY = Deno.env.get('OPEN_ROUTER_API_KEY') || '';
const SUPABASE_URL = Deno.env.get('SUPABASE_URL');
const SUPABASE_SERVICE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

// Initialize Supabase client
const supabase = createClient(SUPABASE_URL!, SUPABASE_SERVICE_KEY!, {
  auth: {
    persistSession: false,
    autoRefreshToken: false
  }
});

// Helper to send Telegram notifications
async function sendTelegramNotification(message: string) {
  try {
    const botToken = Deno.env.get('TELEGRAM_BOT_TOKEN_ATH') || Deno.env.get('TELEGRAM_BOT_TOKEN');
    const chatId = Deno.env.get('TELEGRAM_GROUP_ID_ATH') || Deno.env.get('TELEGRAM_CHAT_ID');
    
    if (!botToken || !chatId) return false;
    
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

// Function to scrape website using ScraperAPI
async function scrapeWebsite(url: string) {
  try {
    console.log(`Scraping website: ${url}`);
    
    // Use JavaScript rendering with wait time for modern SPAs
    const renderUrl = `http://api.scraperapi.com?api_key=${SCRAPERAPI_KEY}&url=${encodeURIComponent(url)}&render=true&wait=3000`;
    
    console.log('Fetching with JavaScript rendering and 3s wait...');
    const response = await fetch(renderUrl, {
      method: 'GET',
      headers: {
        'Accept': 'text/html,application/xhtml+xml'
      }
    });

    if (!response.ok) {
      throw new Error(`ScraperAPI failed: ${response.status}`);
    }

    const html = await response.text();
    
    // Check if we still got minimal content (possible loading state)
    const textContent = html.replace(/<[^>]+>/g, '').trim();
    if (textContent.length < 200) {
      console.log(`Warning: Only ${textContent.length} chars of content after render. Retrying with longer wait...`);
      
      // Try one more time with longer wait
      const longerWaitUrl = `http://api.scraperapi.com?api_key=${SCRAPERAPI_KEY}&url=${encodeURIComponent(url)}&render=true&wait=5000`;
      const retryResponse = await fetch(longerWaitUrl);
      
      if (retryResponse.ok) {
        const retryHtml = await retryResponse.text();
        const retryText = retryHtml.replace(/<[^>]+>/g, '').trim();
        
        if (retryText.length > textContent.length) {
          console.log(`Better result with longer wait: ${retryText.length} chars`);
          return retryHtml;
        }
      }
    }
    
    console.log(`Successfully scraped ${html.length} chars of HTML`);
    return html;
  } catch (error) {
    console.error(`Error scraping website: ${error}`);
    throw error;
  }
}

// Function to parse HTML and extract content with diagnostic metrics
function parseHtmlContent(html: string) {
  const startTime = Date.now();
  
  // Extract text content
  const cleanHtml = html
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '')
    .replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, '');
  
  const textContent = cleanHtml
    .replace(/<[^>]+>/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .substring(0, 15000);
  
  // Check for loading indicators
  const loadIndicators: string[] = [];
  const loadingPatterns = ['Loading...', 'Please wait', 'Initializing', 'Loading', 'One moment', 'Fetching data'];
  loadingPatterns.forEach(pattern => {
    if (textContent.includes(pattern) || html.includes(pattern)) {
      loadIndicators.push(pattern);
    }
  });
  
  // Check if JavaScript heavy (minimal body content but large scripts)
  const bodyMatch = html.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
  const bodyContent = bodyMatch ? bodyMatch[1] : '';
  const scriptCount = (html.match(/<script/gi) || []).length;
  const javascriptHeavy = bodyContent.length < 1000 && scriptCount > 5;
  
  // Extract links with context
  const linkRegex = /<a[^>]*href=["']([^"']+)["'][^>]*>([^<]*)<\/a>/gi;
  const linksWithContext: Array<{url: string, text: string, type: string}> = [];
  const uniqueUrls = new Set<string>();
  let match;
  
  while ((match = linkRegex.exec(cleanHtml)) !== null) {
    const url = match[1];
    const text = match[2].replace(/<[^>]+>/g, '').trim();
    
    if (!uniqueUrls.has(url) && !url.startsWith('#')) {
      uniqueUrls.add(url);
      
      let type = 'other';
      if (/docs|documentation|whitepaper|guide|tutorial|developer|build|resources|learn/i.test(url + ' ' + text)) {
        type = 'documentation';
      } else if (url.includes('github.com') || url.includes('gitlab.com')) {
        type = 'github';
      } else if (/twitter|x\.com|telegram|discord|medium|reddit|linkedin/i.test(url)) {
        type = 'social';
      }
      
      linksWithContext.push({ url, text: text || 'No text', type });
    }
  }
  
  // Extract headers
  const headers: Array<{level: number, text: string}> = [];
  const headerRegex = /<h([1-6])[^>]*>([^<]+)<\/h[1-6]>/gi;
  while ((match = headerRegex.exec(cleanHtml)) !== null) {
    headers.push({
      level: parseInt(match[1]),
      text: match[2].replace(/<[^>]+>/g, '').trim()
    });
  }
  
  // Extract meta tags
  const metaDescription = html.match(/<meta[^>]*name=["']description["'][^>]*content=["']([^"']+)["']/i)?.[1] || '';
  const ogTitle = html.match(/<meta[^>]*property=["']og:title["'][^>]*content=["']([^"']+)["']/i)?.[1] || '';
  const ogDescription = html.match(/<meta[^>]*property=["']og:description["'][^>]*content=["']([^"']+)["']/i)?.[1] || '';
  const metaExists = !!(metaDescription || ogTitle || ogDescription);
  
  // Extract key signals for debugging
  const extractedSignals = {
    partnerships_mentioned: [] as string[],
    user_count_claims: null as string | null,
    funding_mentioned: null as string | null,
    has_whitepaper: false,
    has_github: false,
    team_members_found: 0
  };
  
  // Look for partnerships (NBA, Google, Fortune 500, etc.)
  const partnershipKeywords = ['NBA', 'NFL', 'Google', 'Microsoft', 'Amazon', 'Visa', 'Mastercard', 'Crypto.com', 'Binance', 'Coinbase', 'Samsung', 'Sony', 'Intel', 'Oracle', 'IBM'];
  partnershipKeywords.forEach(partner => {
    if (textContent.includes(partner) || html.includes(partner)) {
      extractedSignals.partnerships_mentioned.push(partner);
    }
  });
  
  // Look for user count claims (102k users, 100,000 users, 1M users, etc.)
  const userMatches = [
    textContent.match(/(\d{1,3}[,.]?\d{0,3})[kKmM]?\+?\s*(users|customers|members|traders|holders|players|participants)/i),
    textContent.match(/(\d{1,3}[,.]?\d{3}[,.]?\d{0,3})\s*(users|customers|members|traders|holders|players|participants)/i),
    textContent.match(/(million|thousand)\s*(users|customers|members|traders|holders|players|participants)/i)
  ];
  
  for (const userMatch of userMatches) {
    if (userMatch) {
      extractedSignals.user_count_claims = userMatch[0];
      break;
    }
  }
  
  // Look for funding mentions
  const fundingMatch = textContent.match(/(\$\d+[kKmMbB]?|\d+\s*(million|billion))\s*(funding|raised|invested|investment|seed|series\s+[a-z])/i);
  if (fundingMatch) {
    extractedSignals.funding_mentioned = fundingMatch[0];
  }
  
  // Check for whitepaper
  extractedSignals.has_whitepaper = linksWithContext.some(l => 
    l.url.toLowerCase().includes('whitepaper') || 
    l.text.toLowerCase().includes('whitepaper') ||
    l.url.toLowerCase().includes('litepaper') ||
    l.text.toLowerCase().includes('litepaper')
  );
  
  // Check for GitHub
  extractedSignals.has_github = linksWithContext.some(l => 
    l.url.includes('github.com') || l.url.includes('gitlab.com')
  );
  
  // Look for team members
  const teamMatch = textContent.match(/team|founder|ceo|cto|developer|engineer|advisor/gi);
  if (teamMatch) {
    extractedSignals.team_members_found = teamMatch.length;
  }
  
  // Build diagnostic metrics
  const diagnostics = {
    text_length: textContent.length,
    html_length: html.length,
    link_count: linksWithContext.length,
    header_count: headers.length,
    has_meta_description: !!metaDescription,
    has_og_tags: !!(ogTitle || ogDescription),
    meta_exists: metaExists,
    load_indicators_found: loadIndicators,
    javascript_heavy: javascriptHeavy,
    script_count: scriptCount,
    body_length: bodyContent.length,
    response_time_ms: Date.now() - startTime,
    scrape_timestamp: new Date().toISOString()
  };
  
  return {
    text_content: textContent,
    links_with_context: linksWithContext.slice(0, 100),
    headers: headers.slice(0, 50),
    meta_tags: {
      description: metaDescription,
      og_title: ogTitle,
      og_description: ogDescription
    },
    text_length: textContent.length,
    diagnostics,  // NEW
    extracted_signals: extractedSignals  // NEW
  };
}

// Function to analyze with AI (Stage 1 analysis)
async function analyzeWithAI(parsedContent: any, ticker: string) {
  const linkSummary = parsedContent.links_with_context?.slice(0, 30).map((l: any) => 
    `[${l.type}] ${l.text}: ${l.url}`
  ).join('\n') || 'No links found';
  
  const headerSummary = parsedContent.headers?.slice(0, 20).map((h: any) => 
    `${'  '.repeat(h.level - 1)}H${h.level}: ${h.text}`
  ).join('\n') || 'No headers found';
  
  const prompt = `Analyze this cryptocurrency project website focusing on LEGITIMACY and REAL-WORLD SIGNALS.

Project: ${ticker}

META INFORMATION:
- Description: ${parsedContent.meta_tags?.description || 'None'}
- OG Title: ${parsedContent.meta_tags?.og_title || 'None'}
- OG Description: ${parsedContent.meta_tags?.og_description || 'None'}

WEBSITE STRUCTURE (Headers):
${headerSummary}

NAVIGATION LINKS (with context):
${linkSummary}

WEBSITE CONTENT (${parsedContent.text_length} chars):
${parsedContent.text_content}

STEP 1 - TOKEN TYPE CLASSIFICATION:
Classify as either:
- "meme": Community/humor/viral FIRST (even if has utility features like staking)
- "utility": Product/service/infrastructure FIRST (even if has meme elements)

STEP 2 - FAST-TRACK CHECK:
Look for extraordinary legitimacy signals. If ANY of these exist, minimum score = 12:
- Partnership with Fortune 500 company or major brand (NBA, Google, etc.)
- Notable VC funding (>$1M verified)
- Proven founder with exit history or notable background
- Government/institutional partnership
- 100k+ verified users/customers
- Any other EXTRAORDINARY signal that would be impossible/extremely costly to fake

If fast-track applies, note which signal(s) triggered it.

STEP 3 - ADAPTIVE SCORING (0-3 each):

IF UTILITY TOKEN - Score these 7 categories:
1. technical_substance: Whitepaper, GitHub, documentation, business model, utility description all combined
   - 0: Nothing substantial explained
   - 1: Basic concept described
   - 2: Detailed docs OR working GitHub OR clear business model
   - 3: Multiple technical proofs present

2. product_evidence: Proof of actual working product/platform
   - 0: Just promises/coming soon
   - 1: Demo/beta/screenshots shown
   - 2: Working product accessible
   - 3: Fully functional with proven usage

3. legitimacy_signals: Unfakeable proofs (partnerships, users, revenue, integrations)
   - 0: No verification possible
   - 1: Some verifiable elements
   - 2: Strong legitimate signals
   - 3: Undeniable proof of legitimacy

4. team_credibility: Who's behind this
   - 0: Fully anonymous
   - 1: Some team info/socials
   - 2: Real identities/LinkedIn
   - 3: Proven track record

5. execution_quality: Professional implementation
   - 0: Template/low effort
   - 1: Basic professional
   - 2: High quality design/UX
   - 3: Enterprise-grade platform

6. fast_track_bonus: Additional points for extraordinary signals
   - 0: No special signals
   - 1-3: Based on strength of fast-track signals found

7. community_traction: Real engagement and adoption
   - 0: Ghost town
   - 1: Some activity
   - 2: Active community (1k-50k users claimed)
   - 3: Massive adoption (50k+ users)

IF MEME TOKEN - Score these 7 categories:
1. community_strength: Social media presence, community links, engagement
2. brand_identity: Memorable concept, clear theme, viral potential
3. website_quality: Professional design, working features, visual appeal
4. authenticity: Original concept vs copycat, unique value proposition
5. transparency: Clear tokenomics, supply info, honest presentation  
6. safety_signals: Contract verification, security measures, liquidity info
7. accessibility: Team communication, clear social links, responsive presence

TIER CLASSIFICATION:
- 0-6: "TRASH" (Poor quality, likely scam)
- 7-11: "BASIC" (Some effort, missing elements)
- 12-17: "SOLID" (Good quality, legitimate project)
- 18+: "ALPHA" (Exceptional project)

Note: Fast-track signals guarantee minimum "SOLID" tier regardless of other scores.

Return JSON only:
{
  "category_scores": {
    "category1_name": 0-3,
    "category2_name": 0-3,
    "category3_name": 0-3,
    "category4_name": 0-3,
    "category5_name": 0-3,
    "category6_name": 0-3,
    "category7_name": 0-3
  },
  "total_score": 0-21,
  "tier": "TRASH/BASIC/SOLID/ALPHA",
  "token_type": "meme/utility",
  "fast_track_triggered": true/false,
  "fast_track_reason": "Brief explanation if triggered",
  "exceptional_signals": ["signal1", "signal2"],
  "missing_elements": ["element1", "element2"],
  "quick_take": "VERY concise summary (max 60 chars)",
  "quick_assessment": "Detailed 2-3 sentence assessment",
  "reasoning": "Brief explanation of tier assignment",
  "type_reasoning": "Why classified as meme or utility"
}`;

  try {
    const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://krom.one',
        'X-Title': 'KROM Discovery Analyzer'
      },
      body: JSON.stringify({
        model: 'moonshotai/kimi-k2',
        messages: [
          {
            role: 'user',
            content: prompt
          }
        ],
        temperature: 0.3,
        max_tokens: 1000,
        response_format: { type: "json_object" }
      })
    });

    if (!response.ok) {
      throw new Error(`AI analysis failed: ${response.status}`);
    }

    const data = await response.json();
    const contentStr = data.choices[0].message.content;
    
    // Parse the JSON response
    let result;
    try {
      result = JSON.parse(contentStr);
    } catch {
      // If that fails, try removing markdown code blocks
      const cleanedContent = contentStr.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
      result = JSON.parse(cleanedContent);
    }
    
    // Apply fast-track minimum if triggered
    if (result.fast_track_triggered && result.total_score < 12) {
      console.log(`Fast-track triggered: Adjusting score from ${result.total_score} to minimum 12`);
      result.total_score = 12;
    }
    
    // Calculate tier based on score (matching production app)
    // Note: Using normalized score out of 10 for tier calculation
    const normalizedScore = Math.round((result.total_score / 21) * 10);
    if (normalizedScore >= 8) result.tier = 'ALPHA';
    else if (normalizedScore >= 6) result.tier = 'SOLID';
    else if (normalizedScore >= 4) result.tier = 'BASIC';
    else result.tier = 'TRASH';
    
    return result;
  } catch (error) {
    console.error(`AI analysis error: ${error}`);
    throw error;
  }
}

// Main function to analyze tokens from discovery
serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    console.log('🔍 Starting token discovery analyzer...');
    
    // Get tokens with websites that need processing:
    // 1. Haven't been analyzed yet (website_analyzed_at IS NULL)
    // 2. OR have been analyzed with score >= 6 (normalizes to ~3) but not promoted yet
    const { data: tokensToProcess, error: fetchError } = await supabase
      .from('token_discovery')
      .select('*')
      .not('website_url', 'is', null)
      .or('website_analyzed_at.is.null,and(website_stage1_score.gte.6,website_analyzed_at.not.is.null)')
      .order('current_liquidity_usd', { ascending: false, nullsFirst: false })
      .limit(1); // Process only 1 at a time

    if (fetchError) {
      throw new Error(`Failed to fetch tokens: ${fetchError.message}`);
    }

    if (!tokensToProcess || tokensToProcess.length === 0) {
      console.log('No tokens with unanalyzed websites found');
      return new Response(JSON.stringify({
        success: true,
        message: 'No tokens to analyze',
        analyzed: 0
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
      });
    }

    console.log(`Found ${tokensToProcess.length} tokens to process`);
    
    const results = {
      analyzed: 0,
      promoted: 0,
      skipped: 0,
      errors: 0,
      promotedTokens: [] as any[]
    };

    for (const token of tokensToProcess) {
      try {
        console.log(`\n🌐 Processing ${token.symbol} (${token.network})`);
        console.log(`   Website: ${token.website_url}`);
        console.log(`   Liquidity: $${token.current_liquidity_usd || token.initial_liquidity_usd}`);
        
        let analysis;
        
        // Check if already analyzed
        if (token.website_stage1_score !== null && token.website_stage1_analysis) {
          console.log(`   Already analyzed: Score ${token.website_stage1_score}/21 (${token.website_stage1_tier})`);
          analysis = {
            total_score: token.website_stage1_score,
            tier: token.website_stage1_tier,
            ...token.website_stage1_analysis
          };
        } else {
          // Step 1: Scrape and analyze website
          console.log(`   Analyzing website...`);
          const html = await scrapeWebsite(token.website_url);
          const parsedContent = parseHtmlContent(html);
          
          // Log diagnostic info for debugging
          console.log(`   Scraped: ${parsedContent.diagnostics.text_length} chars text from ${parsedContent.diagnostics.html_length} chars HTML`);
          if (parsedContent.diagnostics.text_length < 500) {
            console.log(`   ⚠️ WARNING: Very low text content (${parsedContent.diagnostics.text_length} chars)`);
            if (parsedContent.diagnostics.load_indicators_found.length > 0) {
              console.log(`   Loading indicators found: ${parsedContent.diagnostics.load_indicators_found.join(', ')}`);
            }
            if (parsedContent.diagnostics.javascript_heavy) {
              console.log(`   JavaScript-heavy site detected (body: ${parsedContent.diagnostics.body_length} chars, scripts: ${parsedContent.diagnostics.script_count})`);
            }
          }
          
          // Log extracted signals
          if (parsedContent.extracted_signals.partnerships_mentioned.length > 0) {
            console.log(`   🤝 Partnerships detected: ${parsedContent.extracted_signals.partnerships_mentioned.join(', ')}`);
          }
          if (parsedContent.extracted_signals.user_count_claims) {
            console.log(`   👥 User count claim: ${parsedContent.extracted_signals.user_count_claims}`);
          }
          
          analysis = await analyzeWithAI(parsedContent, token.symbol);
          
          console.log(`   Analysis: Score ${analysis.total_score}/21 (${analysis.tier})`);
          console.log(`   Quick take: ${analysis.quick_take}`);
        
          // Step 2: Update token_discovery with analysis results INCLUDING diagnostic data
          const { error: updateError } = await supabase
            .from('token_discovery')
            .update({
              website_analyzed_at: new Date().toISOString(),
              website_stage1_score: analysis.total_score,
              website_stage1_tier: analysis.tier,
              website_stage1_analysis: {
                category_scores: analysis.category_scores,
                token_type: analysis.token_type,
                exceptional_signals: analysis.exceptional_signals,
                missing_elements: analysis.missing_elements,
                quick_take: analysis.quick_take,
                quick_assessment: analysis.quick_assessment,
                reasoning: analysis.reasoning,
                fast_track_triggered: analysis.fast_track_triggered || false,
                fast_track_reason: analysis.fast_track_reason || null,
                // ADD DIAGNOSTIC DATA:
                scrape_metrics: parsedContent.diagnostics,
                extracted_signals: parsedContent.extracted_signals
              }
            })
            .eq('id', token.id);

          if (updateError) {
            console.error(`Failed to update token ${token.id}: ${updateError.message}`);
            results.errors++;
            continue;
          }

          results.analyzed++;
        }

        // Step 3: Check if score qualifies for promotion
        // Lower threshold to 3 (was 4) to catch legitimate projects with real websites
        // Score of 7/21 = 3.3 normalized, which represents a real project
        const normalizedScore = Math.round((analysis.total_score / 21) * 10);
        console.log(`   Normalized score: ${normalizedScore}/10 (from ${analysis.total_score}/21)`);
        
        if (normalizedScore >= 3) {
          console.log(`   ✅ Qualifies for promotion to crypto_calls (normalized score ${normalizedScore}/10 >= 3)`);
          console.log(`   Checking if token already exists in crypto_calls...`);
          console.log(`   Contract: ${token.contract_address}`);
          console.log(`   Network: ${token.network}`);
          
          // Check if already exists in crypto_calls
          const { data: existingCall, error: checkError } = await supabase
            .from('crypto_calls')
            .select('id, contract_address, network')
            .eq('contract_address', token.contract_address)
            .eq('network', token.network)
            .single();

          if (checkError && checkError.code !== 'PGRST116') { // PGRST116 = no rows found
            console.error(`Error checking existing call: ${checkError.message}`);
            results.errors++;
            continue;
          }

          if (existingCall) {
            console.log(`   ⚠️ Token already exists in crypto_calls (ID: ${existingCall.id})`);
            results.skipped++;
            continue;
          }

          // Prepare data for crypto_calls insertion
          const callData = {
            // Core fields
            source: 'new pools',
            contract_address: token.contract_address,
            network: token.network === 'eth' ? 'ethereum' : token.network,
            ticker: token.symbol,
            pool_address: token.pool_address,
            
            // Timestamps (use current time as buy_timestamp since this is when we're "calling" it)
            buy_timestamp: new Date().toISOString(),
            created_at: new Date().toISOString(),
            
            // Market data (with type conversion for text->numeric fields)
            // For initial promotion, all "current" and "at_call" values are the same
            liquidity_usd: parseFloat(token.current_liquidity_usd || token.initial_liquidity_usd || '0'),
            price_at_call: token.current_price_usd ? parseFloat(token.current_price_usd) : null,
            current_price: token.current_price_usd ? parseFloat(token.current_price_usd) : null,
            ath_price: token.current_price_usd ? parseFloat(token.current_price_usd) : null, // Start with current as ATH
            market_cap_at_call: token.current_market_cap ? parseFloat(token.current_market_cap) : null,
            current_market_cap: token.current_market_cap ? parseFloat(token.current_market_cap) : null,
            ath_market_cap: token.current_market_cap ? parseFloat(token.current_market_cap) : null, // Start with current as ATH
            volume_24h: token.current_volume_24h ? parseFloat(token.current_volume_24h) : null,
            
            // Social data
            website_url: token.website_url,
            twitter_url: token.twitter_url,
            telegram_url: token.telegram_url,
            discord_url: token.discord_url,
            socials_fetched_at: new Date().toISOString(),
            
            // Website analysis (already done!)
            website_score: analysis.total_score,
            website_tier: analysis.tier,
            website_token_type: analysis.token_type,
            website_analysis_reasoning: analysis.reasoning,
            website_analysis_full: {
              category_scores: analysis.category_scores,
              token_type: analysis.token_type,
              exceptional_signals: analysis.exceptional_signals,
              missing_elements: analysis.missing_elements,
              quick_take: analysis.quick_take,
              quick_assessment: analysis.quick_assessment,
              reasoning: analysis.reasoning,
              analyzed_at: new Date().toISOString()
            },
            website_analyzed_at: new Date().toISOString(),
            
            // Analysis fields based on website score
            analysis_score: normalizedScore >= 8 ? 8 : normalizedScore >= 6 ? 6 : 4,
            analysis_tier: analysis.tier,
            analysis_token_type: analysis.token_type,  // Use AI's actual classification, not score threshold
            analysis_reasoning: 'Score based on website analysis (discovery token)',
            analyzed_at: new Date().toISOString(),
            
            // Raw data with synthetic call data for compatibility
            raw_data: {
              groupName: 'Discovery Pools',
              token: {
                ca: token.contract_address,
                network: token.network === 'eth' ? 'ethereum' : token.network,
                symbol: token.symbol
              },
              text: 'Token discovered through automated website analysis. High-quality project identified by AI scoring system.',
              timestamp: Math.floor(new Date(token.first_seen_at).getTime() / 1000),
              discovery_id: token.id,
              discovery_data: {
                first_seen_at: token.first_seen_at,
                initial_liquidity: token.initial_liquidity_usd,
                initial_volume: token.initial_volume_24h,
                website_found_at: token.website_found_at,
                website_check_count: token.website_check_count
              }
            }
          };

          // Insert into crypto_calls
          console.log(`   Attempting to insert into crypto_calls...`);
          console.log(`   Buy timestamp: ${callData.buy_timestamp}`);
          console.log(`   Analysis score: ${callData.analysis_score}`);
          
          const { data: newCall, error: insertError } = await supabase
            .from('crypto_calls')
            .insert(callData)
            .select()
            .single();

          if (insertError) {
            console.error(`   ❌ Failed to insert into crypto_calls!`);
            console.error(`   Error code: ${insertError.code}`);
            console.error(`   Error message: ${insertError.message}`);
            console.error(`   Error details: ${JSON.stringify(insertError.details)}`);
            results.errors++;
            continue;
          }

          console.log(`   🎉 Successfully promoted to crypto_calls!`);
          console.log(`   New record ID: ${newCall.id}`);
          results.promoted++;
          results.promotedTokens.push({
            symbol: token.symbol,
            network: token.network,
            score: analysis.total_score,
            tier: analysis.tier,
            quick_take: analysis.quick_take,
            crypto_calls_id: newCall.id
          });

          // Send Telegram notification for promoted tokens
          const liquidityFormatted = new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 0,
            maximumFractionDigits: 0,
          }).format(token.current_liquidity_usd || token.initial_liquidity_usd || 0);

          const message = `🚀 <b>New Discovery Promoted!</b>

<b>${token.symbol}</b> (${token.network.toUpperCase()})
Score: ${analysis.total_score}/21 (${analysis.tier})
Liquidity: ${liquidityFormatted}

${analysis.quick_take}

<a href="${token.website_url}">Website</a> | <a href="https://dexscreener.com/${token.network === 'eth' ? 'ethereum' : token.network}/${token.contract_address}">DexScreener</a>`;

          await sendTelegramNotification(message);
        } else {
          console.log(`   ❌ Score too low for promotion (normalized ${normalizedScore}/10 < 4)`);
          results.skipped++;
        }

      } catch (error) {
        console.error(`Error analyzing token ${token.id}: ${error}`);
        results.errors++;
        
        // Mark as analyzed with error to avoid retrying
        await supabase
          .from('token_discovery')
          .update({
            website_analyzed_at: new Date().toISOString(),
            website_stage1_score: 0,
            website_stage1_tier: 'ERROR',
            website_stage1_analysis: { error: error.message }
          })
          .eq('id', token.id);
      }
    }

    console.log('\n📊 Analysis Summary:');
    console.log(`   Analyzed: ${results.analyzed}`);
    console.log(`   Promoted: ${results.promoted}`);
    console.log(`   Skipped: ${results.skipped}`);
    console.log(`   Errors: ${results.errors}`);

    return new Response(JSON.stringify({
      success: true,
      ...results,
      timestamp: new Date().toISOString()
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });

  } catch (error) {
    console.error('Fatal error in token discovery analyzer:', error);
    return new Response(JSON.stringify({ 
      error: error.message,
      success: false 
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' },
    });
  }
});