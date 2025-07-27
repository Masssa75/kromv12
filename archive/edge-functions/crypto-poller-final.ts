import { serve } from "https://deno.land/std@0.168.0/http/server.ts"
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.7'

const KROM_API_URL = 'https://krom.one/api/v1/calls'

serve(async (req) => {
  try {
    // Create Supabase client with service role
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

    // Get KROM API token
    const kromApiToken = Deno.env.get('KROM_API_TOKEN')
    if (!kromApiToken) {
      throw new Error('KROM_API_TOKEN not configured')
    }

    // Fetch from KROM API
    console.log('Fetching from KROM API...')
    const response = await fetch(KROM_API_URL, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${kromApiToken}`
      }
    })

    if (!response.ok) {
      throw new Error(`KROM API error: ${response.status}`)
    }

    const calls = await response.json()
    console.log(`Fetched ${calls.length} calls from KROM`)

    // Store new calls
    let newCallsCount = 0
    const errors = []

    for (const call of calls) {
      try {
        // Try to insert - if it already exists, it will fail with unique constraint
        const { data, error } = await supabase
          .from('crypto_calls')
          .insert({
            krom_id: call._id,
            ticker: call.token?.symbol || 'UNKNOWN',
            buy_timestamp: call.trade?.buyTimestamp ? new Date(call.trade.buyTimestamp * 1000).toISOString() : null,
            raw_data: call
          })
          .select()

        if (error) {
          if (error.code === '23505') {
            // Unique constraint violation - call already exists
            continue
          } else {
            console.error(`Error inserting call ${call._id}:`, error)
            errors.push({ id: call._id, error: error.message })
          }
        } else {
          newCallsCount++
          console.log(`Added new call: ${call._id} - ${call.token?.symbol || 'Unknown'}`)
        }
      } catch (err) {
        console.error(`Error processing call ${call._id}:`, err)
        errors.push({ id: call._id, error: err.message })
      }
    }

    return new Response(
      JSON.stringify({
        success: true,
        totalFetched: calls.length,
        newCallsAdded: newCallsCount,
        errors: errors.length > 0 ? errors : undefined
      }),
      { headers: { "Content-Type": "application/json" } }
    )
  } catch (error) {
    console.error('Error in crypto-poller:', error)
    return new Response(
      JSON.stringify({
        success: false,
        error: error.message,
        details: error.toString()
      }),
      { 
        status: 500,
        headers: { "Content-Type": "application/json" }
      }
    )
  }
})