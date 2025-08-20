import { serve } from "https://deno.land/std@0.168.0/http/server.ts"

serve(async (req) => {
  try {
    console.log('Crypto Orchestrator Fast starting...');
    const startTime = Date.now();
    
    const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? '';
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? '';
    
    const headers = {
      'Authorization': `Bearer ${supabaseKey}`,
      'Content-Type': 'application/json',
    };

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

    // Step 2: Analyze new calls with Claude (SKIP X ANALYSIS)
    console.log('Step 2: Analyzing calls with Claude...');
    const analyzerStart = Date.now();
    const analyzerResponse = await fetch(`${supabaseUrl}/functions/v1/crypto-analyzer`, {
      method: 'POST',
      headers
    });
    const analyzerResult = await analyzerResponse.json();
    const analyzerTime = Date.now() - analyzerStart;
    console.log(`Analyzer completed in ${analyzerTime}ms:`, analyzerResult);

    // Step 3: Send notifications (premium only)
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
    console.log(`Total orchestration time: ${totalTime}ms`);

    return new Response(
      JSON.stringify({
        success: true,
        timestamp: new Date().toISOString(),
        timing: {
          total: totalTime,
          poller: pollerTime,
          analyzer: analyzerTime,
          notifier: notifierTime
        },
        results: {
          poller: pollerResult,
          analyzer: analyzerResult,
          notifier: notifierResult
        }
      }),
      { headers: { "Content-Type": "application/json" } }
    );

  } catch (error) {
    console.error('Orchestrator error:', error);
    return new Response(
      JSON.stringify({
        success: false,
        error: error.message,
        timestamp: new Date().toISOString()
      }),
      { 
        status: 500,
        headers: { "Content-Type": "application/json" }
      }
    );
  }
});