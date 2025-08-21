import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.7';

// Constants
const SCRAPERAPI_KEY = Deno.env.get('SCRAPERAPI_KEY') || '';
const OPENROUTER_API_KEY = Deno.env.get('OPEN_ROUTER_API_KEY') || '';
const SUPABASE_URL = Deno.env.get('SUPABASE_URL');
const SUPABASE_SERVICE_KEY = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');

// Check for required environment variables
if (!SUPABASE_URL || !SUPABASE_SERVICE_KEY) {
  console.error('Missing required environment variables:');
  console.error('SUPABASE_URL:', SUPABASE_URL ? 'Present' : 'MISSING');
  console.error('SUPABASE_SERVICE_ROLE_KEY:', SUPABASE_SERVICE_KEY ? 'Present' : 'MISSING');
}

// Initialize Supabase client
const supabase = createClient(SUPABASE_URL!, SUPABASE_SERVICE_KEY!, {
  auth: {
    persistSession: false,
    autoRefreshToken: false
  }
});

// Category weights for scoring
const CATEGORY_WEIGHTS = {
  technical_infrastructure: 3,
  business_utility: 3,
  documentation_quality: 3,
  community_social: 3,
  security_trust: 3,
  team_transparency: 3,
  website_presentation: 3
};

// Function to scrape website using ScraperAPI
async function scrapeWebsite(url: string) {
  try {
    console.log(`Scraping website: ${url}`);
    
    // Always use JavaScript rendering with wait time for modern SPAs
    // This ensures we get the full content, not just loading screens
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
      console.log(`Warning: Only ${textContent.length} chars of content after render. Possible loading screen.`);
      
      // Try one more time with longer wait
      const longerWaitUrl = `http://api.scraperapi.com?api_key=${SCRAPERAPI_KEY}&url=${encodeURIComponent(url)}&render=true&wait=5000`;
      console.log('Retrying with 5s wait...');
      
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

// Function to parse HTML and extract content
function parseHtmlContent(html: string) {
  // Extract text content (remove scripts and styles first)
  const cleanHtml = html
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '') // Remove scripts
    .replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, ''); // Remove styles
  
  const textContent = cleanHtml
    .replace(/<[^>]+>/g, ' ') // Remove HTML tags
    .replace(/\s+/g, ' ') // Normalize whitespace
    .trim()
    .substring(0, 15000); // Increased to 15k for better context
  
  // Extract ALL links with their text context
  const linkRegex = /<a[^>]*href=["']([^"']+)["'][^>]*>([^<]*)<\/a>/gi;
  const linksWithContext: Array<{url: string, text: string, type: string}> = [];
  const uniqueUrls = new Set<string>();
  let match;
  
  while ((match = linkRegex.exec(cleanHtml)) !== null) {
    const url = match[1];
    const text = match[2].replace(/<[^>]+>/g, '').trim();
    
    // Skip duplicates and anchors
    if (!uniqueUrls.has(url) && !url.startsWith('#')) {
      uniqueUrls.add(url);
      
      // Categorize the link type
      let type = 'other';
      if (/docs|documentation|whitepaper|guide|tutorial|developer|build|resources|learn/i.test(url + ' ' + text)) {
        type = 'documentation';
      } else if (url.includes('github.com') || url.includes('gitlab.com')) {
        type = 'github';
      } else if (/twitter|x\.com|telegram|discord|medium|reddit|linkedin/i.test(url)) {
        type = 'social';
      } else if (/about|team|partners|investors/i.test(url + ' ' + text)) {
        type = 'about';
      } else if (/blog|news|updates|announcements/i.test(url + ' ' + text)) {
        type = 'blog';
      }
      
      linksWithContext.push({ url, text: text || 'No text', type });
    }
  }
  
  // Also extract button links (modern sites use buttons for navigation)
  const buttonRegex = /<button[^>]*onclick=["'][^"']*["'][^>]*>([^<]*)<\/button>/gi;
  const buttonTexts: string[] = [];
  while ((match = buttonRegex.exec(cleanHtml)) !== null) {
    const buttonText = match[1].replace(/<[^>]+>/g, '').trim();
    if (buttonText) buttonTexts.push(buttonText);
  }
  
  // Extract headers to understand page structure
  const headers: Array<{level: number, text: string}> = [];
  const headerRegex = /<h([1-6])[^>]*>([^<]+)<\/h[1-6]>/gi;
  while ((match = headerRegex.exec(cleanHtml)) !== null) {
    headers.push({
      level: parseInt(match[1]),
      text: match[2].replace(/<[^>]+>/g, '').trim()
    });
  }
  
  // Extract meta tags for additional context
  const metaDescription = html.match(/<meta[^>]*name=["']description["'][^>]*content=["']([^"']+)["']/i)?.[1] || '';
  const metaKeywords = html.match(/<meta[^>]*name=["']keywords["'][^>]*content=["']([^"']+)["']/i)?.[1] || '';
  const ogTitle = html.match(/<meta[^>]*property=["']og:title["'][^>]*content=["']([^"']+)["']/i)?.[1] || '';
  const ogDescription = html.match(/<meta[^>]*property=["']og:description["'][^>]*content=["']([^"']+)["']/i)?.[1] || '';
  
  // Check for React/Next.js __NEXT_DATA__ (often contains pre-loaded content)
  const nextDataMatch = html.match(/<script[^>]*id="__NEXT_DATA__"[^>]*>([^<]+)<\/script>/i);
  let hasNextData = false;
  let nextDataPreview = '';
  if (nextDataMatch) {
    hasNextData = true;
    try {
      const nextData = JSON.parse(nextDataMatch[1]);
      // Extract a preview of the data (first 500 chars)
      nextDataPreview = JSON.stringify(nextData).substring(0, 500);
    } catch (e) {
      // Invalid JSON, ignore
    }
  }
  
  // Build categorized link summary for backward compatibility
  const categorizedLinks = {
    documentation: linksWithContext.filter(l => l.type === 'documentation').map(l => l.url),
    github: linksWithContext.filter(l => l.type === 'github').map(l => l.url),
    social: linksWithContext.filter(l => l.type === 'social').map(l => l.url),
    all_links: linksWithContext.slice(0, 150) // Increased limit
  };
  
  return {
    text_content: textContent,
    navigation: categorizedLinks,
    links_with_context: linksWithContext.slice(0, 100), // New: links with their text
    headers: headers.slice(0, 50), // New: page structure
    button_texts: buttonTexts.slice(0, 20), // New: button navigation
    meta_tags: { // New: meta information
      description: metaDescription,
      keywords: metaKeywords,
      og_title: ogTitle,
      og_description: ogDescription
    },
    content_length: html.length,
    text_length: textContent.length, // New: actual text length
    has_documentation: categorizedLinks.documentation.length > 0,
    has_github: categorizedLinks.github.length > 0,
    has_social: categorizedLinks.social.length > 0,
    has_next_data: hasNextData, // New: React/Next.js app indicator
    next_data_preview: nextDataPreview // New: preview of Next.js data
  };
}

// Function to analyze with AI
async function analyzeWithAI(parsedContent: any, ticker: string) {
  // Create a summary of links with their context
  const linkSummary = parsedContent.links_with_context?.slice(0, 30).map((l: any) => 
    `[${l.type}] ${l.text}: ${l.url}`
  ).join('\n') || 'No links found';
  
  // Create a summary of headers
  const headerSummary = parsedContent.headers?.slice(0, 20).map((h: any) => 
    `${'  '.repeat(h.level - 1)}H${h.level}: ${h.text}`
  ).join('\n') || 'No headers found';
  
  const prompt = `Analyze this cryptocurrency project website using ADAPTIVE SCORING based on token type.

Project: ${ticker}

META INFORMATION:
- Description: ${parsedContent.meta_tags?.description || 'None'}
- OG Title: ${parsedContent.meta_tags?.og_title || 'None'}
- OG Description: ${parsedContent.meta_tags?.og_description || 'None'}

WEBSITE STRUCTURE (Headers):
${headerSummary}

NAVIGATION LINKS (with context):
${linkSummary}

BUTTON NAVIGATION:
${parsedContent.button_texts?.join(', ') || 'None found'}

WEBSITE CONTENT (${parsedContent.text_length} chars):
${parsedContent.text_content}

IMPORTANT: Look at ALL the links above - many documentation links might be at /developers, /build, /resources, etc. not just /docs.
Check the link text and context carefully before determining if documentation exists.

STEP 1 - TOKEN TYPE CLASSIFICATION:
First classify this token as either:
- "meme": Community-driven, humor/viral focus, animal/cartoon themes, "to the moon" rhetoric, cultural references, primarily speculation/entertainment
- "utility": Clear use case, solving real problems, technical infrastructure, business model, professional presentation, actual product/service

STEP 2 - ADAPTIVE SCORING (0-3 each category):

IF MEME TOKEN - Score these 7 categories:
1. community_strength: Social media presence, community links, engagement indicators, active following
2. brand_identity: Memorable concept, clear theme/character, viral potential, cultural relevance
3. website_quality: Professional design, working features, visual appeal, user experience
4. authenticity: Original concept vs copycat, unique value proposition, creative execution
5. transparency: Clear tokenomics, supply info, no hidden mechanics, honest presentation  
6. safety_signals: Contract verification mentioned, security measures, liquidity info, trust indicators
7. accessibility: Team communication, community access, clear social links, responsive presence

IF UTILITY TOKEN - Score these 7 categories:
1. technical_infrastructure: GitHub repos, APIs, developer resources, technical depth
2. business_utility: Real use case, problem-solving, market need, practical application
3. documentation_quality: Whitepapers, technical docs, guides, comprehensive information
4. community_social: Active community, social presence, user engagement, ecosystem
5. security_trust: Audits, security info, transparency measures, risk mitigation
6. team_transparency: Team info, backgrounds, LinkedIn, credentials, accountability
7. website_presentation: Professional design, working features, technical presentation

Also identify:
- Exceptional signals (major partnerships, high revenue, large user base, unique achievements)
- Critical missing elements (what's lacking for this token type)
- Should this proceed to deeper Stage 2 analysis?

TIER CLASSIFICATION (0-21 total):
- 0-7: "TRASH" (Poor quality, likely scam or very low effort)
- 8-14: "BASIC" (Some effort, but missing key elements for its type)
- 15-20: "SOLID" (Good quality, professional, most important elements present)
- 21: "ALPHA" (Exceptional, all elements perfect for its type)

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
  "exceptional_signals": ["signal1", "signal2"],
  "missing_elements": ["element1", "element2"],
  "proceed_to_stage_2": true/false,
  "stage_2_links": ["url1", "url2", "url3"],
  "quick_assessment": "Detailed 2-3 sentence assessment explaining the score in context of token type",
  "reasoning": "Brief explanation of tier assignment",
  "type_reasoning": "Why classified as meme or utility with key indicators"
}`;

  try {
    const response = await fetch('https://openrouter.ai/api/v1/chat/completions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${OPENROUTER_API_KEY}`,
        'Content-Type': 'application/json',
        'HTTP-Referer': 'https://krom.one',
        'X-Title': 'KROM Website Analyzer'
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
    
    // Parse the JSON response (handle if it's wrapped in markdown code blocks)
    let result;
    try {
      // First try direct parse
      result = JSON.parse(contentStr);
    } catch {
      // If that fails, try removing markdown code blocks
      const cleanedContent = contentStr.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
      result = JSON.parse(cleanedContent);
    }
    
    // Calculate tier based on score (using new tier names)
    if (result.total_score >= 21) result.tier = 'ALPHA';
    else if (result.total_score >= 15) result.tier = 'SOLID';
    else if (result.total_score >= 8) result.tier = 'BASIC';
    else result.tier = 'TRASH';
    
    return result;
  } catch (error) {
    console.error(`AI analysis error: ${error}`);
    throw error;
  }
}

serve(async (req) => {
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  };

  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    const { url, ticker, callId } = await req.json();
    
    if (!url || !ticker) {
      throw new Error('Missing required parameters: url and ticker');
    }

    console.log(`Analyzing website for ${ticker}: ${url}`);

    // Step 1: Scrape website
    const html = await scrapeWebsite(url);
    
    // Step 2: Parse content
    const parsedContent = parseHtmlContent(html);
    console.log(`Parsed ${parsedContent.text_length} chars of text from ${parsedContent.content_length} chars of HTML`);
    console.log(`Found ${parsedContent.links_with_context?.length || 0} links, ${parsedContent.headers?.length || 0} headers`);
    
    // Step 3: Analyze with AI
    const analysis = await analyzeWithAI(parsedContent, ticker);
    console.log(`Analysis complete: Score ${analysis.total_score}/21 (${analysis.tier})`);
    
    // Step 4: Update database if callId provided
    let updateSuccess = false;
    let updateError = null;
    
    if (callId) {
      console.log(`Updating database for ${ticker} with ID ${callId}`);
      console.log(`Service key length: ${SUPABASE_SERVICE_KEY?.length || 0}`);
      console.log(`URL: ${SUPABASE_URL}`);
      
      try {
        // Create comprehensive analysis object for JSONB column
        const fullAnalysis = {
          category_scores: analysis.category_scores,
          exceptional_signals: analysis.exceptional_signals || [],
          missing_elements: analysis.missing_elements || [],
          quick_assessment: analysis.quick_assessment || analysis.reasoning,
          proceed_to_stage_2: analysis.proceed_to_stage_2,
          stage_2_links: analysis.stage_2_links || [],
          parsed_content: parsedContent,
          navigation_links: parsedContent.navigation,
          type_reasoning: analysis.type_reasoning
        };
        
        const updatePayload = {
          website_score: analysis.total_score,
          website_tier: analysis.tier,
          website_token_type: analysis.token_type,
          website_analysis_reasoning: analysis.reasoning,
          website_analysis_full: fullAnalysis,  // Store everything in JSONB
          website_analyzed_at: new Date().toISOString()
        };
        
        console.log('Update payload ready, executing...');
        
        const { data, error } = await supabase
          .from('crypto_calls')
          .update(updatePayload)
          .eq('id', callId)
          .select();
        
        if (error) {
          updateError = error;
          console.error('Database update FAILED:', error);
          console.error('Error code:', error.code);
          console.error('Error message:', error.message);
          console.error('Full error:', JSON.stringify(error, null, 2));
        } else {
          updateSuccess = true;
          console.log(`✅ Database UPDATE SUCCESS for ${ticker}`);
          console.log('Updated data:', JSON.stringify(data, null, 2));
        }
      } catch (err) {
        updateError = err;
        console.error('Exception during update:', err);
      }
    } else {
      console.log('No callId provided, skipping database update');
    }
    
    // Return analysis results
    return new Response(
      JSON.stringify({
        success: true,
        ticker,
        url,
        score: analysis.total_score,
        tier: analysis.tier,
        token_type: analysis.token_type,
        category_scores: analysis.category_scores,
        stage2_qualified: analysis.proceed_to_stage_2,
        exceptional_signals: analysis.exceptional_signals,
        reasoning: analysis.reasoning,
        type_reasoning: analysis.type_reasoning,
        database_update: {
          attempted: !!callId,
          success: updateSuccess,
          error: updateError ? updateError.message : null
        },
        content_stats: {
          content_length: parsedContent.content_length,
          total_links: parsedContent.navigation.all_links.length,
          has_documentation: parsedContent.has_documentation,
          has_github: parsedContent.has_github
        }
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 200
      }
    );
    
  } catch (error) {
    console.error('Error in crypto-website-analyzer:', error);
    
    return new Response(
      JSON.stringify({ 
        success: false, 
        error: error.message 
      }),
      {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' },
        status: 500
      }
    );
  }
});