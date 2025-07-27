import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.7'

const X_ANALYSIS_PROMPT = `You are analyzing tweets about a cryptocurrency token. Based on the tweets provided, you need to:

1. Determine the quality tier (ALPHA, SOLID, BASIC, or TRASH)
2. Create a bullet-point summary of key information
3. Identify any red flags

Tier Criteria:
- ALPHA: Strong project fundamentals, notable team/backers, clear utility, significant partnerships
- SOLID: Good project description, some team info, community engagement, legitimate use case
- BASIC: Minimal project info, generic descriptions, standard hype
- TRASH: No meaningful info, only spam/bot posts, or no tweets found

Focus on:
- What the project does
- Who's behind it
- Notable supporters
- Partnerships
- Red flags (keep separate)

Response format:
TIER: [ALPHA/SOLID/BASIC/TRASH]
SUMMARY:
• [Key point 1]
• [Key point 2]
• [Key point 3]
RED FLAGS:
• [Red flag 1]
• [Red flag 2]`

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

    // Get API keys
    const xBearerToken = Deno.env.get('X_BEARER_TOKEN')
    const anthropicApiKey = Deno.env.get('ANTHROPIC_API_KEY')
    
    if (!xBearerToken || !anthropicApiKey) {
      throw new Error('X or Anthropic API credentials not configured')
    }

    // Fetch unanalyzed calls (no X analysis yet)
    const { data: unanalyzedCalls, error: fetchError } = await supabase
      .from('crypto_calls')
      .select('*')
      .is('x_analyzed_at', null)
      .not('raw_data->token->ca', 'is', null)
      .order('buy_timestamp', { ascending: false })
      .limit(10)

    if (fetchError) {
      throw fetchError
    }

    console.log(`Found ${unanalyzedCalls?.length || 0} calls to analyze on X`)

    const analysisResults = []
    const errors = []

    for (const call of unanalyzedCalls || []) {
      try {
        const contractAddress = call.raw_data?.token?.ca
        if (!contractAddress) {
          console.log(`No contract address for ${call.krom_id}`)
          continue
        }

        // Search X for the contract address
        const xSearchUrl = `https://api.twitter.com/2/tweets/search/recent`
        const params = new URLSearchParams({
          query: contractAddress,
          'tweet.fields': 'public_metrics,created_at,author_id',
          'max_results': '5', // Only fetch top 5 posts to save API quota
          'sort_order': 'relevancy' // This gets us "popular" tweets
        })

        const xResponse = await fetch(`${xSearchUrl}?${params}`, {
          headers: {
            'Authorization': `Bearer ${xBearerToken}`
          }
        })

        if (!xResponse.ok) {
          throw new Error(`X API error: ${xResponse.status}`)
        }

        const xData = await xResponse.json()
        const tweets = xData.data || []

        // Filter tweets with at least 1 retweet AND 1 like
        const qualityTweets = tweets.filter((tweet: any) => 
          tweet.public_metrics.retweet_count >= 1 && 
          tweet.public_metrics.like_count >= 1
        )

        // Sort by engagement (likes + retweets)
        qualityTweets.sort((a: any, b: any) => {
          const aEngagement = a.public_metrics.like_count + a.public_metrics.retweet_count
          const bEngagement = b.public_metrics.like_count + b.public_metrics.retweet_count
          return bEngagement - aEngagement
        })

        // Take top 20 most engaged tweets
        const topTweets = qualityTweets.slice(0, 20)

        let tier = 'TRASH'
        let summary = ''
        let redFlags = ''

        if (topTweets.length === 0) {
          if (tweets.length === 0) {
            summary = '• No tweets found for this contract address'
          } else {
            summary = '• Only spam/low-quality tweets found'
          }
        } else {
          // Prepare tweets for Claude analysis
          const tweetContent = topTweets.map((tweet: any) => 
            `[${tweet.public_metrics.like_count} likes, ${tweet.public_metrics.retweet_count} retweets] ${tweet.text}`
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
          tweetsAnalyzed: topTweets.length
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