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

        // For now, since Nitter is having issues, let's do a simplified analysis
        // without X data - mark everything as needing manual review
        console.log(`Analyzing ${contractAddress} without X data due to API issues`)
        
        const tier = 'BASIC'
        const summary = '• X analysis unavailable - manual review needed\n• Contract address found\n• No tweet data available'
        const redFlags = '• Cannot verify social presence'

        // Store analysis results
        const { error: updateError } = await supabase
          .from('crypto_calls')
          .update({
            x_analysis_tier: tier,
            x_analysis_summary: summary + `\nRED FLAGS:\n${redFlags}`,
            x_raw_tweets: [],
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
          tweetsAnalyzed: 0,
          source: 'fallback'
        })

        console.log(`Fallback analysis complete for ${call.ticker} (${call.krom_id})`)

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