import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.7'

serve(async (req) => {
  try {
    const supabaseUrl = Deno.env.get('SUPABASE_URL') ?? ''
    const supabaseKey = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    
    // Create admin client for calling other Edge Functions
    const headers = {
      'Authorization': `Bearer ${supabaseKey}`,
      'Content-Type': 'application/json'
    }

    const startTime = Date.now()
    console.log('Starting crypto orchestrator with timing...')

    // Step 1: Poll for new calls
    console.log('Step 1: Polling for new calls...')
    const pollerStart = Date.now()
    const pollerResponse = await fetch(`${supabaseUrl}/functions/v1/crypto-poller`, {
      method: 'POST',
      headers
    })
    const pollerResult = await pollerResponse.json()
    const pollerTime = Date.now() - pollerStart
    console.log(`Poller completed in ${pollerTime}ms:`, pollerResult)

    // Step 2: Analyze unanalyzed calls
    console.log('Step 2: Analyzing calls...')
    const analyzerStart = Date.now()
    const analyzerResponse = await fetch(`${supabaseUrl}/functions/v1/crypto-analyzer`, {
      method: 'POST',
      headers
    })
    const analyzerResult = await analyzerResponse.json()
    const analyzerTime = Date.now() - analyzerStart
    console.log(`Analyzer completed in ${analyzerTime}ms:`, analyzerResult)

    // Step 3: Send notifications for analyzed calls
    console.log('Step 3: Sending notifications...')
    const notifierStart = Date.now()
    const notifierResponse = await fetch(`${supabaseUrl}/functions/v1/crypto-notifier`, {
      method: 'POST',
      headers
    })
    const notifierResult = await notifierResponse.json()
    const notifierTime = Date.now() - notifierStart
    console.log(`Notifier completed in ${notifierTime}ms:`, notifierResult)

    const totalTime = Date.now() - startTime
    console.log(`Total orchestrator time: ${totalTime}ms`)

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
    )

  } catch (error) {
    console.error('Error in crypto-orchestrator:', error)
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