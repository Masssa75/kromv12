import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.7'

const X_ANALYSIS_PROMPT = `Analyze these crypto tweets and provide ULTRA-CONCISE insights.

TIER: Choose ONE: ALPHA, SOLID, BASIC, or TRASH

SUMMARY: Maximum 3 bullet points, 10 words each:
• Project purpose (if found)
• Team/backers (if notable)  
• Key detail (if any)

RED FLAGS: Maximum 2 points, 5 words each:
• Main concern
• Secondary risk

Keep it EXTREMELY brief. No fluff. Facts only.`

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

    // Get Anthropic API key
    const anthropicApiKey = Deno.env.get('ANTHROPIC_API_KEY')
    
    if (!anthropicApiKey) {
      throw new Error('Anthropic API key not configured')
    }

    // Fetch unanalyzed calls
    const { data: unanalyzedCalls, error: fetchError } = await supabase
      .from('crypto_calls')
      .select('*')
      .is('x_analyzed_at', null)
      .not('raw_data->token->ca', 'is', null)
      .order('buy_timestamp', { ascending: false })
      .limit(5)

    if (fetchError) {
      throw fetchError
    }

    console.log(`Found ${unanalyzedCalls?.length || 0} calls to analyze`)

    const analysisResults = []
    const errors = []

    for (const call of unanalyzedCalls || []) {
      try {
        const contractAddress = call.raw_data?.token?.ca
        if (!contractAddress) {
          console.log(`No contract address for ${call.krom_id}`)
          continue
        }

        console.log(`Searching for contract: ${contractAddress}`)
        
        // Try different approach - use cors-proxy.com
        const nitterUrl = `https://nitter.net/search?q=${contractAddress}&f=tweets`
        const proxyUrl = `https://cors-proxy.elfsight.com/${encodeURIComponent(nitterUrl)}`
        
        console.log(`Fetching via proxy: ${proxyUrl}`)
        
        const response = await fetch(proxyUrl, {
          headers: {
            'User-Agent': 'Mozilla/5.0 (compatible; CryptoAnalyzer/1.0)',
          }
        })
        
        if (!response.ok) {
          throw new Error(`Proxy responded with status: ${response.status}`)
        }

        const html = await response.text()
        console.log(`Received HTML response, length: ${html.length}`)

        // Check if we got a valid response
        if (html.length < 1000) {
          throw new Error(`Response too short: ${html.substring(0, 200)}`)
        }

        // Extract tweets using regex
        const tweetMatches = html.matchAll(/<div class="tweet-content[^"]*"[^>]*>([\s\S]*?)<\/div>/gi)
        const tweets = []

        for (const match of tweetMatches) {
          const content = match[1]
            .replace(/<[^>]*>/g, ' ') // Remove HTML tags
            .replace(/\s+/g, ' ') // Normalize whitespace
            .trim()
          
          if (content && content.length > 20) {
            tweets.push({ text: content })
          }
          
          if (tweets.length >= 5) break
        }

        // If no tweets found with first pattern, try alternative pattern
        if (tweets.length === 0) {
          const altMatches = html.matchAll(/<div[^>]*class="[^"]*content[^"]*"[^>]*>([\s\S]*?)<\/div>/gi)
          for (const match of altMatches) {
            const content = match[1]
              .replace(/<[^>]*>/g, ' ')
              .replace(/\s+/g, ' ')
              .trim()
            
            if (content && content.includes(contractAddress)) {
              tweets.push({ text: content })
            }
            
            if (tweets.length >= 5) break
          }
        }

        console.log(`Found ${tweets.length} tweets for ${contractAddress}`)

        let tier = 'TRASH'
        let summary = ''
        let redFlags = ''

        if (tweets.length === 0) {
          summary = '• No tweets found for this contract address'
        } else {
          // Prepare tweets for Claude analysis
          const tweetContent = tweets.map((tweet, index) => 
            `Tweet ${index + 1}: ${tweet.text}`
          ).join('\n\n')

          // Call Claude to analyze the tweets
          const anthropicResponse = await fetch('https://api.anthropic.com/v1/messages', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'x-api-key': anthropicApiKey,
              'anthropic-version': '2023-06-01'
            },
            body: JSON.stringify({
              model: 'claude-3-haiku-20240307',
              max_tokens: 500,
              temperature: 0,
              system: X_ANALYSIS_PROMPT,
              messages: [
                {
                  role: 'user',
                  content: `Analyze these tweets about contract address ${contractAddress}:\n\n${tweetContent}`
                }
              ]
            })
          })

          if (!anthropicResponse.ok) {
            throw new Error(`Claude API error: ${anthropicResponse.status}`)
          }

          const anthropicResult = await anthropicResponse.json()
          const analysisText = anthropicResult.content[0].text

          // Parse Claude's response
          const tierMatch = analysisText.match(/TIER:\s*(\w+)/)
          const summaryMatch = analysisText.match(/SUMMARY:\s*([\s\S]*?)(?=RED FLAGS:|$)/)
          const redFlagsMatch = analysisText.match(/RED FLAGS:\s*([\s\S]*)/)

          tier = tierMatch ? tierMatch[1].toUpperCase() : 'TRASH'
          summary = summaryMatch ? summaryMatch[1].trim() : '• Unable to analyze tweets'
          redFlags = redFlagsMatch ? redFlagsMatch[1].trim() : ''
        }

        // Store analysis results
        const { error: updateError } = await supabase
          .from('crypto_calls')
          .update({
            x_analysis_tier: tier,
            x_analysis_summary: summary + (redFlags ? `\nRED FLAGS:\n${redFlags}` : ''),
            x_raw_tweets: tweets.slice(0, 5),
            x_analyzed_at: new Date().toISOString()
          })
          .eq('krom_id', call.krom_id)

        if (updateError) {
          throw updateError
        }

        analysisResults.push({
          krom_id: call.krom_id,
          ticker: call.ticker,
          tier: tier,
          tweetsAnalyzed: tweets.length,
          source: 'cors-proxy'
        })

        console.log(`X analysis complete for ${call.ticker} (${call.krom_id}): ${tier}`)

      } catch (error) {
        console.error(`Error analyzing ${call.krom_id}:`, error)
        errors.push({
          krom_id: call.krom_id,
          error: error.message
        })
      }
    }

    return new Response(
      JSON.stringify({
        success: true,
        analyzed: analysisResults.length,
        results: analysisResults,
        errors: errors.length > 0 ? errors : undefined
      }),
      { headers: { "Content-Type": "application/json" } }
    )

  } catch (error) {
    console.error('Error in crypto-x-analyzer:', error)
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