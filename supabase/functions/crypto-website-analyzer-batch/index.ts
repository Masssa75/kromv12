import { serve } from "https://deno.land/std@0.168.0/http/server.ts";
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.7';

serve(async (req) => {
  const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
  };

  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders });
  }

  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL');
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
    
    if (!supabaseUrl || !supabaseKey) {
      throw new Error('Missing required environment variables');
    }

    // Initialize Supabase client
    const supabase = createClient(supabaseUrl, supabaseKey, {
      auth: {
        persistSession: false,
        autoRefreshToken: false
      }
    });

    console.log('Starting batch website analysis...');

    // Find calls with websites but no analysis
    const { data: callsToAnalyze, error: fetchError } = await supabase
      .from('crypto_calls')
      .select('id, ticker, website_url')
      .not('website_url', 'is', null)
      .is('website_score', null)
      .limit(5); // Match the KROM poller intake limit

    if (fetchError) {
      throw new Error(`Failed to fetch calls: ${fetchError.message}`);
    }

    if (!callsToAnalyze || callsToAnalyze.length === 0) {
      console.log('No calls with websites need analysis');
      return new Response(JSON.stringify({
        success: true,
        message: 'No calls need website analysis',
        analyzed: 0
      }), {
        headers: { ...corsHeaders, 'Content-Type': 'application/json' }
      });
    }

    console.log(`Found ${callsToAnalyze.length} calls to analyze - processing in parallel`);

    // Process all calls in parallel using Promise.allSettled
    const analysisPromises = callsToAnalyze.map(async (call) => {
      try {
        console.log(`Starting analysis for ${call.ticker}: ${call.website_url}`);
        
        // Call the individual website analyzer with a timeout
        const analyzerResponse = await Promise.race([
          fetch(`${supabaseUrl}/functions/v1/crypto-website-analyzer`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${supabaseKey}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              callId: call.id,
              ticker: call.ticker,
              url: call.website_url
            })
          }),
          // Timeout after 60 seconds per website (increased for slow sites)
          new Promise((_, reject) => 
            setTimeout(() => reject(new Error('Timeout after 60s')), 60000)
          )
        ]);

        if (!analyzerResponse.ok) {
          console.error(`Failed to analyze ${call.ticker}: ${analyzerResponse.status}`);
          return {
            ticker: call.ticker,
            success: false,
            error: `HTTP ${analyzerResponse.status}`
          };
        }
        
        const analyzerResult = await analyzerResponse.json();
        console.log(`Successfully analyzed ${call.ticker}: Score ${analyzerResult.score}/21 (${analyzerResult.tier})`);
        return {
          ticker: call.ticker,
          success: true,
          score: analyzerResult.score,
          tier: analyzerResult.tier,
          type: analyzerResult.token_type
        };
      } catch (error) {
        console.error(`Error analyzing ${call.ticker}:`, error.message);
        return {
          ticker: call.ticker,
          success: false,
          error: error.message
        };
      }
    });

    // Wait for all analyses to complete (or fail)
    const analysisResults = await Promise.allSettled(analysisPromises);
    
    // Extract results from Promise.allSettled
    const results = analysisResults.map((result, index) => {
      if (result.status === 'fulfilled') {
        return result.value;
      } else {
        return {
          ticker: callsToAnalyze[index].ticker,
          success: false,
          error: result.reason?.message || 'Unknown error'
        };
      }
    });

    const successCount = results.filter(r => r.success).length;
    console.log(`Batch analysis complete: ${successCount}/${results.length} successful`);

    return new Response(JSON.stringify({
      success: true,
      analyzed: successCount,
      total: results.length,
      results: results
    }), {
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });

  } catch (error) {
    console.error('Error in batch website analyzer:', error);
    return new Response(JSON.stringify({
      success: false,
      error: error.message
    }), {
      status: 500,
      headers: { ...corsHeaders, 'Content-Type': 'application/json' }
    });
  }
});