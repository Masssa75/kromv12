import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

serve(async (req)=>{
  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? '';
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '';
    // Create admin client for calling other Edge Functions
    const headers = {
      'Authorization': `Bearer ${supabaseKey}`,
      'Content-Type': 'application/json'
    };
    const startTime = Date.now();
    console.log('Starting crypto orchestrator with X analysis...');
    // Step 1: Poll for new calls
    console.log('Step 1: Polling for new calls...');
    const pollerStart = Date.now();
    const pollerResponse = await fetch(`${supabaseUrl}/functions/v1/crypto-poller`, {
      method: 'POST',
      headers
    });
    const pollerResult = await pollerResponse.json();
    const pollerTime = Date.now() - pollerStart;
    console.log(`Poller completed in ${pollerTime}ms:`, pollerResult);
    // Step 2: Run Claude and X analysis in parallel
    console.log('Step 2: Running parallel analysis (Claude + X)...');
    const analysisStart = Date.now();
    const [analyzerResponse, xAnalyzerResponse] = await Promise.all([
      fetch(`${supabaseUrl}/functions/v1/crypto-analyzer`, {
        method: 'POST',
        headers
      }),
      fetch(`${supabaseUrl}/functions/v1/crypto-x-analyzer-nitter`, {
        method: 'POST',
        headers
      })
    ]);
    const analyzerResult = await analyzerResponse.json();
    const xAnalyzerResult = await xAnalyzerResponse.json();
    const analysisTime = Date.now() - analysisStart;
    console.log(`Analysis completed in ${analysisTime}ms`);
    console.log(`Claude analyzer:`, analyzerResult);
    console.log(`X analyzer:`, xAnalyzerResult);
    // Step 3: Send notifications for analyzed calls
    console.log('Step 3: Sending notifications...');
    const notifierStart = Date.now();
    const notifierResponse = await fetch(`${supabaseUrl}/functions/v1/crypto-notifier-complete`, {
      method: 'POST',
      headers
    });
    const notifierResult = await notifierResponse.json();
    const notifierTime = Date.now() - notifierStart;
    console.log(`Notifier completed in ${notifierTime}ms:`, notifierResult);
    const totalTime = Date.now() - startTime;
    console.log(`Total orchestrator time: ${totalTime}ms`);
    return new Response(JSON.stringify({
      success: true,
      timestamp: new Date().toISOString(),
      timing: {
        total: totalTime,
        poller: pollerTime,
        analysis: analysisTime,
        notifier: notifierTime
      },
      results: {
        poller: pollerResult,
        analyzer: analyzerResult,
        xAnalyzer: xAnalyzerResult,
        notifier: notifierResult
      }
    }), {
      headers: {
        "Content-Type": "application/json"
      }
    });
  } catch (error) {
    console.error('Error in crypto-orchestrator:', error);
    return new Response(JSON.stringify({
      success: false,
      error: error.message
    }), {
      status: 500,
      headers: {
        "Content-Type": "application/json"
      }
    });
  }
});