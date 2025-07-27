import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.7'
import { DOMParser } from "https://deno.land/x/deno_dom/deno-dom-wasm.ts"

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

// List of Nitter instances (use multiple for redundancy)
const NITTER_INSTANCES = [
  'https://nitter.net',
  'https://nitter.poast.org',
  'https://nitter.privacydev.net',
  'https://nitter.woodland.cafe'
]

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
      .limit(5) // Process 5 at a time

    if (fetchError) {
      throw fetchError
    }

    console.log(`Found ${unanalyzedCalls?.length || 0} calls to analyze via Nitter`)

    const analysisResults = []
    const errors = []

    for (const call of unanalyzedCalls || []) {
      try {
        const contractAddress = call.raw_data?.token?.ca
        if (!contractAddress) {
          console.log(`No contract address for ${call.krom_id}`)
          continue
        }

        // Try multiple Nitter instances until one works
        let searchResults = null
        let workingInstance = null

        for (const instance of NITTER_INSTANCES) {
          try {
            console.log(`Trying Nitter instance: ${instance}`)
            const searchUrl = `${instance}/search?q=${contractAddress}&f=tweets`
            
            const response = await fetch(searchUrl, {
              headers: {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
              }
            })

            if (response.ok) {
              searchResults = await response.text()
              workingInstance = instance
              break
            }
          } catch (error) {
            console.log(`Failed to fetch from ${instance}:`, error)
            continue
          }
        }

        if (!searchResults) {
          throw new Error('All Nitter instances failed')
        }

        // Parse HTML to extract tweets
        const parser = new DOMParser()
        const doc = parser.parseFromString(searchResults, 'text/html')
        
        // Extract tweet content
        const tweets = []
        const tweetElements = doc.querySelectorAll('.timeline-item')
        
        tweetElements.forEach((element, index) => {
          if (index >= 10) return // Only take first 10 tweets
          
          const content = element.querySelector('.tweet-content')?.textContent || ''
          const stats = element.querySelector('.tweet-stats')
          
          // Extract engagement metrics
          const replies = stats?.querySelector('.icon-comment')?.parentElement?.textContent || '0'
          const retweets = stats?.querySelector('.icon-retweet')?.parentElement?.textContent || '0'
          const likes = stats?.querySelector('.icon-heart')?.parentElement?.textContent || '0'
          
          // Only include tweets with some engagement
          const likeCount = parseInt(likes) || 0
          const retweetCount = parseInt(retweets) || 0
          
          if (likeCount > 0 || retweetCount > 0) {
            tweets.push({
              text: content.trim(),
              likes: likeCount,
              retweets: retweetCount,
              engagement: likeCount + retweetCount
            })
          }
        })

        // Sort by engagement and take top 5
        tweets.sort((a, b) => b.engagement - a.engagement)
        const topTweets = tweets.slice(0, 5)

        let tier = 'TRASH'
        let summary = ''
        let redFlags = ''

        if (topTweets.length === 0) {
          summary = '• No tweets found for this contract address'
        } else {
          // Prepare tweets for Claude analysis
          const tweetContent = topTweets.map(tweet => 
            `[${tweet.likes} likes, ${tweet.retweets} retweets] ${tweet.text}`
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
            x_raw_tweets: topTweets,
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
          tweetsAnalyzed: topTweets.length,
          source: 'nitter'
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