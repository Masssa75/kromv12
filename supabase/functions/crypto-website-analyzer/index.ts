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
    
    // Try simple fetch first
    const scraperUrl = `http://api.scraperapi.com?api_key=${SCRAPERAPI_KEY}&url=${encodeURIComponent(url)}`;
    
    const response = await fetch(scraperUrl, {
      method: 'GET',
      headers: {
        'Accept': 'text/html,application/xhtml+xml'
      }
    });

    if (!response.ok) {
      console.log(`ScraperAPI simple fetch failed: ${response.status}, trying with render...`);
      
      // Fallback to JavaScript rendering
      const renderUrl = `http://api.scraperapi.com?api_key=${SCRAPERAPI_KEY}&url=${encodeURIComponent(url)}&render=true`;
      const renderResponse = await fetch(renderUrl);
      
      if (!renderResponse.ok) {
        throw new Error(`ScraperAPI failed: ${renderResponse.status}`);
      }
      
      return await renderResponse.text();
    }

    const html = await response.text();
    
    // Check if we got a loading screen (less than 500 chars of actual content)
    const textContent = html.replace(/<[^>]+>/g, '').trim();
    if (textContent.length < 500 && html.includes('javascript')) {
      console.log('Detected JavaScript-heavy site, retrying with render...');
      
      // Retry with rendering
      const renderUrl = `http://api.scraperapi.com?api_key=${SCRAPERAPI_KEY}&url=${encodeURIComponent(url)}&render=true`;
      const renderResponse = await fetch(renderUrl);
      
      if (renderResponse.ok) {
        const renderHtml = await renderResponse.text();
        if (renderHtml.length > html.length) {
          return renderHtml;
        }
      }
    }
    
    return html;
  } catch (error) {
    console.error(`Error scraping website: ${error}`);
    throw error;
  }
}

// Function to parse HTML and extract content
function parseHtmlContent(html: string) {
  // Extract text content (simple regex-based approach for Edge Function)
  const textContent = html
    .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '') // Remove scripts
    .replace(/<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>/gi, '') // Remove styles
    .replace(/<[^>]+>/g, ' ') // Remove HTML tags
    .replace(/\s+/g, ' ') // Normalize whitespace
    .trim()
    .substring(0, 10000); // Limit to 10k chars for AI analysis
  
  // Extract links (simplified extraction)
  const linkRegex = /href=["'](https?:\/\/[^"']+)["']/gi;
  const links: string[] = [];
  let match;
  
  while ((match = linkRegex.exec(html)) !== null) {
    links.push(match[1]);
  }
  
  // Categorize links
  const categorizedLinks = {
    documentation: links.filter(l => 
      /docs|documentation|whitepaper|guide|tutorial/i.test(l)
    ),
    github: links.filter(l => l.includes('github.com')),
    social: links.filter(l => 
      /twitter|telegram|discord|medium|reddit/i.test(l)
    ),
    all_links: links.slice(0, 100) // Limit to 100 links
  };
  
  return {
    text_content: textContent,
    navigation: categorizedLinks,
    content_length: html.length,
    has_documentation: categorizedLinks.documentation.length > 0,
    has_github: categorizedLinks.github.length > 0,
    has_social: categorizedLinks.social.length > 0
  };
}

// Function to analyze with AI
async function analyzeWithAI(parsedContent: any, ticker: string) {
  const prompt = `Analyze this cryptocurrency project website for investment potential.

Project: ${ticker}

Website Content:
${parsedContent.text_content}

Navigation Links Found:
- Documentation: ${parsedContent.navigation.documentation.length} links
- GitHub: ${parsedContent.navigation.github.length} links  
- Social: ${parsedContent.navigation.social.length} links

Score each category from 0-3:
1. technical_infrastructure (GitHub, APIs, developer resources)
2. business_utility (Real use case, solving actual problems)
3. documentation_quality (Whitepapers, technical docs, guides)
4. community_social (Active community, social presence)
5. security_trust (Audits, security info, transparency)
6. team_transparency (Team info, backgrounds, LinkedIn)
7. website_presentation (Professional design, working features)

Also identify:
- Exceptional signals (e.g., major partnerships, high revenue, large user base)
- Critical missing elements
- Should this proceed to deeper Stage 2 analysis?
- If Stage 2 is recommended, list 3-5 specific URLs from the website that would be most valuable to analyze deeper (docs, GitHub, whitepaper, etc.)

TOKEN TYPE CLASSIFICATION:
Based on the website content, classify this token as either:
- "meme": Community-driven, humor/viral focus, no real utility, animal/cartoon themes, "to the moon" rhetoric, primarily speculation-based
- "utility": Clear use case, solving real problems, technical infrastructure, business model, professional presentation, actual product/service

Choose the PRIMARY nature - if it has both elements, pick the dominant one.

TIER CLASSIFICATION:
Based on total score (0-21):
- 0-7: "TRASH" (Poor quality, likely scam or low effort)
- 8-14: "BASIC" (Some effort, but lacking key elements)
- 15-20: "SOLID" (Good quality, professional, most elements present)
- 21: "ALPHA" (Exceptional, all elements perfect)

Return JSON only:
{
  "category_scores": {
    "technical_infrastructure": 0-3,
    "business_utility": 0-3,
    "documentation_quality": 0-3,
    "community_social": 0-3,
    "security_trust": 0-3,
    "team_transparency": 0-3,
    "website_presentation": 0-3
  },
  "total_score": 0-21,
  "tier": "TRASH/BASIC/SOLID/ALPHA",
  "token_type": "meme/utility",
  "exceptional_signals": ["signal1", "signal2"],
  "missing_elements": ["element1", "element2"],
  "proceed_to_stage_2": true/false,
  "stage_2_links": ["url1", "url2", "url3"],
  "quick_assessment": "Detailed 2-3 sentence assessment",
  "reasoning": "Brief explanation",
  "type_reasoning": "Why classified as meme or utility"
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
    console.log(`Parsed ${parsedContent.content_length} chars, found ${parsedContent.navigation.all_links.length} links`);
    
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